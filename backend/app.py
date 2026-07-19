import json
import hashlib
import re
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from sentence_transformers import SentenceTransformer, util
import ollama
import random

app = Flask(__name__)
CORS(app)

LOG_FILE = "memory_log.json"
USERS_FILE = "users.json"
TOP_K = 5
MIN_SCORE = 0.15
SUMMARY_TRIGGERS = ["how was my day", "what did i do today", "summarize my day", "recap my day", "what happened today"]

print("Loading embedding model...")
embed_model = SentenceTransformer("all-MiniLM-L6-v2")


# ---------- Identity / canned answers ----------

IDENTITY_RESPONSES = {
    r"\b(who|what) are you\b": "I'm Cortex — your personal memory assistant. I quietly remember what you've seen throughout your day, so you can ask me things like \"where did I leave my keys\" or \"what did I do this morning.\"",
    r"\bwhat do you do\b": "I capture short moments from your day, describe them, and let you ask questions about them later in plain English — like a second memory you can talk to.",
    r"\bhow do you work\b": "A camera captures moments, an AI describes each one in a sentence, and when you ask a question, I find the most relevant memories and answer using only what was actually seen.",
    r"\bare you (an ai|a bot|real)\b": "Yes, I'm an AI assistant — I don't have memories of my own, only the ones captured from your day.",
    r"\bdo you store (my )?(photos|images|video)\b": "No — I only ever store short text descriptions of what was seen, never raw photos or video. That's a core part of how I'm designed.",
}


def check_identity_question(query):
    q = query.lower().strip()
    for pattern, response in IDENTITY_RESPONSES.items():
        if re.search(pattern, q):
            return response
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


def is_summary_question(query):
    q = query.lower().strip()
    return any(trigger in q for trigger in SUMMARY_TRIGGERS)


def get_todays_memories(memories):
    today = datetime.now().date()
    todays = [m for m in memories if datetime.fromisoformat(m["timestamp"]).date() == today]
    todays.sort(key=lambda m: m["timestamp"])
    return todays


def retrieve_memories(query, memories):
    if not memories:
        return []
    captions = [m["caption"] for m in memories]
    caption_embeddings = embed_model.encode(captions, convert_to_tensor=True)
    query_embedding = embed_model.encode(query, convert_to_tensor=True)
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


def build_prompt(query, retrieved, is_summary=False):
    context_lines = [f"- {humanize_timestamp(m['timestamp'])}, saw: {m['caption']}" for m in retrieved]
    context = "\n".join(context_lines)

    pov_rules = """POV rules:
- If a memory describes hands, an object being held, or a close-up view, that is the user's OWN point of view — describe it as "you were holding/using..." (first person, direct).
- If a memory describes a full person, that is someone ELSE the camera saw — describe it as "you saw someone..." (third person, about another person).
- Never refer to the user themselves as "someone" or "the person" — the user is always "you"."""

    base_rules = """Rules:
- Write your answer as natural, flowing spoken sentences — the way a person would casually tell a friend. NEVER use bullet points, asterisks, dashes, or a "Key related memories:" style list.
- Weave the time naturally into the sentence (e.g. "Around 3 PM, you had your laptop out on your desk") instead of stating it separately.
- Only use facts directly stated in the memories. Do not invent objects, actions, locations, or events.
- If you're not fully certain, say so naturally in the sentence itself (e.g. "I'm not totally sure, but the last time I saw it was...") rather than listing raw memory fragments.
- Keep it to 1-3 sentences, conversational and confident, not robotic."""

    if is_summary:
        return f"""You are Cortex, a personal memory assistant speaking directly to the user.

Below is every memory captured today, in chronological order.

{pov_rules}

{base_rules}
- For this "how was my day" style question, narrate it like a brief, natural recap — a short paragraph, not a list.

Today's memories:
{context}

Question: {query}

Answer:"""

    return f"""You are Cortex, a personal memory assistant speaking directly to the user.

The memories below are listed in the order they happened, judged most relevant to the question.

{pov_rules}

{base_rules}

Memories:
{context}

Question: {query}

Answer:"""

    return f"""You are Cortex, a personal memory assistant speaking directly to the user.

The memories below are listed in the order they happened, judged most relevant to the question.

{pov_rules}

{base_rules}
- If unsure these memories answer the question, say so, then list the key related memories with times instead of guessing.

Memories:
{context}

Question: {query}

Answer:"""


def generate_answer(prompt):
    response = ollama.generate(model="llama3.2", prompt=prompt, options={"temperature": 0.1})
    return response["response"].strip()


@app.route("/api/query", methods=["POST"])
def query():
    data = request.json
    username = data.get("username")
    user_query = data.get("query", "").strip()

    if not username or not user_query:
        return jsonify({"error": "Missing username or query"}), 400

    identity_answer = check_identity_question(user_query)
    if identity_answer:
        return jsonify({"answer": identity_answer})
    identity_answer = check_identity_question(user_query)
    if identity_answer:
        return jsonify({"answer": identity_answer})

    social_answer = check_social_question(user_query)
    if social_answer:
        return jsonify({"answer": social_answer})

    memories = get_user_memories(username)

    if is_summary_question(user_query):
        todays = get_todays_memories(memories)
        if not todays:
            return jsonify({"answer": "I don't have any memories from today."})
        prompt = build_prompt(user_query, todays, is_summary=True)
    else:
        retrieved = retrieve_memories(user_query, memories)
        if not retrieved:
            return jsonify({"answer": "I don't have any memory related to that."})
        prompt = build_prompt(user_query, retrieved, is_summary=False)

    answer = generate_answer(prompt)
    return jsonify({"answer": answer})
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


def check_social_question(query):
    import random
    q = query.lower().strip()
    for pattern, responses in SOCIAL_RESPONSES.items():
        if re.search(pattern, q):
            return random.choice(responses)
    return None


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

    # Generate suggestions
    suggestions = []
    candidates = [
        f"{username}2026",
        f"{username}{random.randint(10, 99)}",
        f"{username}_{random.randint(1, 999)}",
        f"the_{username}",
        f"{username}_official",
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

    # Take a spread of distinct moments across the day (max 5)
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


if __name__ == "__main__":
    app.run(debug=True, port=5001)