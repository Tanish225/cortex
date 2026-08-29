import json
import hashlib
import re
import random
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from sentence_transformers import SentenceTransformer, util
import torch
import ollama
import os
from live_capture import capture_and_process
from transformers import BlipProcessor, BlipForConditionalGeneration

# this automatically finds the folder the script is running in
BASE_DIR = os.path.dirname(os.path.abspath(__file__))   

app = Flask(__name__)
CORS(app)

LOG_FILE = os.path.join(BASE_DIR, "memory_log.json")
USERS_FILE = os.path.join(BASE_DIR, "users.json")
TOP_K = 5
MIN_SCORE = 0.15
SUMMARY_TRIGGERS = [
    "how was my day",
    "what did i do today",
    "summarize my day",
    "recap my day",
    "what happened today",
    "give me more details of my day",
    "tell me about my day",
    "more details of my day"
]

print("Loading AI embedding model...")
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

print("Loading Vision AI model (this takes a few seconds)...")
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")


# ---------- Identity / canned answers ----------

IDENTITY_RESPONSES = {
    r"\b(who|what) are you\b": "I'm Cortex — your personal memory assistant. I quietly remember what you've seen throughout your day, so you can ask me things like \"where did I leave my keys\" or \"what did I do this morning.\"",
    r"\bwhat do you do\b": "I capture short moments from your day, describe them, and let you ask questions about them later in plain English — like a second memory you can talk to.",
    r"\bhow do you work\b": "A camera captures moments, an AI describes each one in a sentence, and when you ask a question, I find the most relevant memories and answer using only what was actually seen.",
    r"\bare you (an ai|a bot|real)\b": "Yes, I'm an AI assistant — I don't have memories of my own, only the ones captured from your day.",
    r"\bdo you store (my )?(photos|images|video)\b": "No — I only ever store short text descriptions of what was seen, never raw photos or video. That's a core part of how I'm designed.",
    r"\bwho made you\b": "Tanish Sinha, Vani Goel and Glenn Monteiro designed me.",
}

SOCIAL_RESPONSES = {
    r"^(thank you|thanks|thank u|thx|ty)[\s!.]*$": [
        "You're welcome!",
        "Anytime!",
        "Happy to help.",
    ],
    r"^(ok|okay|alright|got it|cool|nice|great)[\s!.]*$": [
        "👍",
        "Sounds good.",
    ],
    r"^(bye|goodbye|see you|see ya)[\s!.]*$": [
        "See you later!",
        "Take care!",
    ],
    r"^(good morning|good afternoon|good evening|good night)[\s!.]*$": [
        "Hope it's a good one!",
    ],
}


def check_identity_question(query_text):
    q = query_text.lower().strip()
    for pattern, response in IDENTITY_RESPONSES.items():
        if re.search(pattern, q):
            return response
    return None


def check_social_question(query_text):
    q = query_text.lower().strip()
    for pattern, responses in SOCIAL_RESPONSES.items():
        if re.search(pattern, q):
            return random.choice(responses)
    return None


# ---------- Auth ----------

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.json
    username, password = data.get("username", "").strip(), data.get("password", "")
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    users = load_users()
    if username in users:
        return jsonify({"error": "Username already exists"}), 400

    users[username] = hash_password(password)
    save_users(users)
    return jsonify({"success": True})


@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    username, password = data.get("username", "").strip(), data.get("password", "")

    users = load_users()
    if username not in users or users[username] != hash_password(password):
        return jsonify({"error": "Incorrect username or password"}), 401

    return jsonify({"success": True, "username": username})


# ---------- Memory helpers (per-user) ----------

def load_memory_log():
    try:
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def save_memory_log(memory_log):
    with open(LOG_FILE, "w") as f:
        json.dump(memory_log, f, indent=2)


def get_user_memories(username):
    """Only returns memories owned by this user. Memories without an 'owner' field are treated as legacy/shared test data."""
    all_memories = load_memory_log()
    return [m for m in all_memories if m.get("owner", username) == username]


def humanize_timestamp(ts_string):
    dt = datetime.fromisoformat(ts_string)
    now = datetime.now()
    if dt.date() == now.date():
        day_part = "today"
    elif (now.date() - dt.date()).days == 1:
        day_part = "yesterday"
    else:
        day_part = dt.strftime("%B %d")
    time_part = dt.strftime("%I:%M %p").lstrip("0")
    return f"{day_part} at {time_part}"


def is_summary_question(query_text):
    q = query_text.lower().strip()
    return any(trigger in q for trigger in SUMMARY_TRIGGERS)


def get_todays_memories(memories):
    today = datetime.now().date()
    todays = [m for m in memories if datetime.fromisoformat(m["timestamp"]).date() == today]
    todays.sort(key=lambda m: m["timestamp"])
    return todays


def retrieve_memories(query_text, memories):
    """Finds the top-k most relevant memories. Uses cached embeddings stored at capture
    time when available, only computing (and backfilling) embeddings for older entries
    that don't have one yet — this avoids re-embedding every memory on every query."""
    if not memories:
        return []

    needs_backfill = False
    embeddings_list = []
    for m in memories:
        if "embedding" in m:
            embeddings_list.append(m["embedding"])
        else:
            emb = embed_model.encode(m["caption"]).tolist()
            m["embedding"] = emb
            embeddings_list.append(emb)
            needs_backfill = True

    if needs_backfill:
        all_memories = load_memory_log()
        lookup = {(m["filename"], m["timestamp"]): m for m in memories}
        for entry in all_memories:
            key = (entry["filename"], entry["timestamp"])
            if key in lookup and "embedding" not in entry:
                entry["embedding"] = lookup[key]["embedding"]
        with open(LOG_FILE, "w") as f:
            json.dump(all_memories, f, indent=2)

    query_embedding = embed_model.encode(query_text, convert_to_tensor=True)
    caption_embeddings = torch.tensor(embeddings_list).to(query_embedding.device)
    scores = util.cos_sim(query_embedding, caption_embeddings)[0]

    top_results = scores.topk(min(TOP_K, len(memories)))
    retrieved = []
    for score, idx in zip(top_results.values, top_results.indices):
        idx = idx.item()
        retrieved.append({
            "caption": memories[idx]["caption"],
            "timestamp": memories[idx]["timestamp"],
            "score": score.item()
        })
    retrieved = [m for m in retrieved if m["score"] > MIN_SCORE]
    retrieved.sort(key=lambda m: m["timestamp"])
    return retrieved


REMEMBER_PATTERN = r"^remember (that )?(.+)"


def check_remember_command(query_text):
    match = re.match(REMEMBER_PATTERN, query_text.strip(), re.IGNORECASE)
    if match:
        return match.group(2).strip()
    return None


def save_note(username, note_text):
    """Stores an explicitly user-stated fact as a memory, same shape as captured memories,
    so it can be found later through normal retrieval — but tagged as a note, not a captured moment."""
    all_memories = load_memory_log()
    timestamp = datetime.now().isoformat()
    caption = f"You said: {note_text}"
    embedding = embed_model.encode(caption).tolist()

    all_memories.append({
        "filename": None,
        "caption": caption,
        "timestamp": timestamp,
        "embedding": embedding,
        "owner": username,
        "source": "note"
    })

    with open(LOG_FILE, "w") as f:
        json.dump(all_memories, f, indent=2)


FORGET_PATTERN = r"^(forget|delete)( that| the memory( that| about)?)? (.+)"


def check_forget_command(query_text):
    match = re.match(FORGET_PATTERN, query_text.strip(), re.IGNORECASE)
    if match:
        return match.group(4).strip()
    return None


def delete_memory_by_query(username, target_text):
    """Finds the single best-matching memory for this user and removes it entirely."""
    memories = get_user_memories(username)
    if not memories:
        return None

    query_embedding = embed_model.encode(target_text, convert_to_tensor=True)
    embeddings_list = [m["embedding"] for m in memories if "embedding" in m]
    if not embeddings_list:
        return None
    caption_embeddings = torch.tensor(embeddings_list).to(query_embedding.device)
    scores = util.cos_sim(query_embedding, caption_embeddings)[0]
    best_idx = scores.argmax().item()
    best_score = scores[best_idx].item()

    if best_score < MIN_SCORE:
        return None

    target = memories[best_idx]

    all_memories = load_memory_log()
    all_memories = [
        m for m in all_memories
        if not (m["filename"] == target.get("filename") and m["timestamp"] == target["timestamp"])
    ]

    save_memory_log(all_memories)
    return target["caption"]


def build_prompt(query_text, retrieved, is_summary=False, support_mode=False):
    context_lines = [f"- {humanize_timestamp(m['timestamp'])}, saw: {m['caption']}" for m in retrieved]
    context = "\n".join(context_lines)

    pov_rules = '''POV Rules (CRITICAL):
- The camera is worn on your face. 
- If a memory describes "a hand", "hands", or an object being held close up, IT IS YOUR HAND. You MUST say "You were holding..." or "You had...". 
- Do not say "you saw a hand" or "someone else" unless the memory explicitly says "a person" or "someone".
- Translating "a hand" to "your hand" is REQUIRED and is NOT considered hallucinating.'''

    if support_mode:
        return f"""You are Cortex, speaking gently to someone who finds complex sentences hard to follow.

Rules:
- Use very simple words and short sentences, no more than 10-12 words each.
- Be warm, calm, and reassuring in tone, like a kind friend.
- Avoid only using exact clock times — say "earlier today" or "a little while ago" also mention of "3:42 PM" if make sense.
- Never imply the person forgot something or should have remembered — just answer plainly and kindly.
- State the one key fact clearly. Do not add extra details, lists, or context that isn't needed.
- Only use facts directly in the memories below. Never invent anything.

{pov_rules}

Memories:
{context}

Question: {query_text}

Answer:"""

    base_rules = """Rules:
- STRICT FACT-CHECKING: You are strictly forbidden from inventing details, locations, or actions. You must ONLY state what is written, while following the POV rules above.
- Write your answer as natural, flowing spoken sentences. NEVER use bullet points.
- Weave the time naturally into the sentence (e.g. "Around 7:42 AM, you...").
- Keep your answer concise if the memory is short."""

    if is_summary:
        return f"""You are Cortex, a personal memory assistant speaking directly to the user.

Below is every memory captured today, in chronological order.

{pov_rules}

{base_rules}
- For this "how was my day" style question, narrate it like a brief, natural recap — a short paragraph, not a list.

Today's memories:
{context}

Question: {query_text}

Answer:"""

    return f"""You are Cortex, a personal memory assistant speaking directly to the user.

The memories below are listed in the order they happened, judged most relevant to the question.

{pov_rules}

{base_rules}
- If unsure these memories answer the question, say so, then briefly mention the related memories naturally, instead of guessing.

Memories:
{context}

Question: {query_text}

Answer:"""


def generate_answer(prompt, support_mode=False):
    temperature = 0.05 if support_mode else 0.1
    response = ollama.generate(model="llama3.2", prompt=prompt, options={"temperature": temperature})
    return response["response"].strip()


@app.route("/api/query", methods=["POST"])
def query():
    data = request.json
    username = data.get("username")
    user_query = data.get("query", "").strip()
    support_mode = data.get("support_mode", False)

    if not username or not user_query:
        return jsonify({"error": "Missing username or query"}), 400

    identity_answer = check_identity_question(user_query)
    if identity_answer:
        return jsonify({"answer": identity_answer})
    
    social_answer = check_social_question(user_query)
    if social_answer:
        return jsonify({"answer": social_answer})

    note_text = check_remember_command(user_query)
    if note_text:
        save_note(username, note_text)
        confirmation = f"Got it — I'll remember that {note_text}."
        return jsonify({"answer": confirmation})

    forget_text = check_forget_command(user_query)
    if forget_text:
        deleted_caption = delete_memory_by_query(username, forget_text)
        if deleted_caption:
            return jsonify({"answer": "Done — I've forgotten that memory."})
        else:
            return jsonify({"answer": "I couldn't find a memory matching that, so nothing was deleted."})

    memories = get_user_memories(username)

    if is_summary_question(user_query):
        todays = get_todays_memories(memories)
        if not todays:
            msg = "Nothing yet today." if support_mode else "I don't have any memories from today."
            return jsonify({"answer": msg})
        prompt = build_prompt(user_query, todays, is_summary=True, support_mode=support_mode)
    else:
        retrieved = retrieve_memories(user_query, memories)
        if not retrieved:
            msg = "I don't know that one yet." if support_mode else "I don't have any memory related to that."
            return jsonify({"answer": msg})
        prompt = build_prompt(user_query, retrieved, is_summary=False, support_mode=support_mode)

    answer = generate_answer(prompt, support_mode=support_mode)
    return jsonify({"answer": answer})


# ---------- Memory Management API ----------

@app.route("/api/memories", methods=["GET"])
def get_memories():
    username = request.args.get("username")
    if not username:
        return jsonify({"error": "Missing username"}), 400

    memories = get_user_memories(username)
    formatted = [
        {
            "id": m["timestamp"],
            "caption": m["caption"],
            "display_time": humanize_timestamp(m["timestamp"]),
            "source": m.get("source", "capture")
        }
        for m in reversed(memories)
    ]
    return jsonify({"memories": formatted})

@app.route("/api/memories", methods=["POST"])
def add_memory_item():
    data = request.json
    username = data.get("username")
    caption = data.get("caption", "").strip()

    if not username or not caption:
        return jsonify({"error": "Missing username or caption"}), 400

    # We can reuse the existing save_note helper to embed and store it
    save_note(username, caption)
    return jsonify({"success": True})


@app.route("/api/memories/<path:memory_id>", methods=["PUT"])
def update_memory_item(memory_id):
    data = request.json
    new_caption = data.get("caption", "").strip()

    if not new_caption:
        return jsonify({"error": "Caption cannot be empty"}), 400

    all_memories = load_memory_log()
    for m in all_memories:
        if m["timestamp"] == memory_id:
            m["caption"] = new_caption
            m["embedding"] = embed_model.encode(new_caption).tolist()
            save_memory_log(all_memories)
            return jsonify({"success": True})

    return jsonify({"error": "Memory not found"}), 404


@app.route("/api/memories/<path:memory_id>", methods=["DELETE"])
def delete_memory_item(memory_id):
    all_memories = load_memory_log()
    updated = [m for m in all_memories if m["timestamp"] != memory_id]

    if len(all_memories) == len(updated):
        return jsonify({"error": "Memory not found"}), 404

    save_memory_log(updated)
    return jsonify({"success": True})


@app.route("/api/memory-count", methods=["GET"])
def memory_count():
    username = request.args.get("username")
    memories = get_user_memories(username)
    return jsonify({"count": len(memories)})


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/check-username", methods=["GET"])
def check_username():
    username = request.args.get("username", "").strip()
    if not username:
        return jsonify({"available": False, "suggestions": []})

    users = load_users()

    if username not in users:
        return jsonify({"available": True, "suggestions": []})

    suggestions = []
    candidates = [
        f"{username}2026",
        f"{username}{random.randint(10, 99)}",
        f"{username}_{random.randint(1, 999)}",
        f"the_{username}_official",
        f"the_{username}",
    ]
    for c in candidates:
        if c not in users and c not in suggestions:
            suggestions.append(c)
        if len(suggestions) >= 3:
            break

    return jsonify({"available": False, "suggestions": suggestions})


@app.route("/api/highlights", methods=["GET"])
def highlights():
    username = request.args.get("username")
    memories = get_user_memories(username)
    todays = get_todays_memories(memories)

    if not todays:
        return jsonify({"highlights": [], "date": datetime.now().strftime("%A, %B %d")})

    step = max(1, len(todays) // 5)
    sample = todays[::step][:5]

    highlight_list = [
        {"caption": m["caption"], "time": humanize_timestamp(m["timestamp"])}
        for m in sample
    ]

    return jsonify({
        "highlights": highlight_list,
        "date": datetime.now().strftime("%A, %B %d")
    })
    
@app.route('/api/capture', methods=['POST'])
def api_capture():
    data = request.json
    username = data.get('username')
    
    if not username:
        return jsonify({"error": "No user logged in"}), 400

    # This turns on the camera, processes the memory, and drops the photo
    new_memory = capture_and_process(username, embed_model, processor, model)
    
    if new_memory:
        return jsonify({"message": "Memory captured successfully!", "memory": new_memory}), 200
    else:
        return jsonify({"error": "Camera failed"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5001)