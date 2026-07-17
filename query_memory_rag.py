import json
import ollama
from datetime import datetime
from sentence_transformers import SentenceTransformer, util

LOG_FILE = "memory_log.json"
TOP_K = 5
MIN_SCORE = 0.15

# Keywords that trigger a "summarize my day" style answer instead of similarity search
SUMMARY_TRIGGERS = ["how was my day", "what did i do today", "summarize my day", "recap my day", "what happened today"]


def load_models():
    print("Loading search model...")
    embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    return embed_model


def load_memory_log():
    with open(LOG_FILE, "r") as f:
        return json.load(f)


def humanize_timestamp(ts_string):
    """Convert '2026-07-10T21:55:55.452011' into something like 'today at 9:55 PM'."""
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


def get_todays_memories(memory_log):
    """Returns every memory captured today, sorted chronologically."""
    today = datetime.now().date()
    todays = [
        m for m in memory_log
        if datetime.fromisoformat(m["timestamp"]).date() == today
    ]
    todays.sort(key=lambda m: m["timestamp"])
    return todays


def retrieve_memories(query, memory_log, embed_model, caption_embeddings):
    """Finds the top-k most relevant memories for a given question."""
    query_embedding = embed_model.encode(query, convert_to_tensor=True)
    scores = util.cos_sim(query_embedding, caption_embeddings)[0]

    top_results = scores.topk(min(TOP_K, len(memory_log)))

    retrieved = []
    for score, idx in zip(top_results.values, top_results.indices):
        idx = idx.item()
        retrieved.append({
            "caption": memory_log[idx]["caption"],
            "timestamp": memory_log[idx]["timestamp"],
            "score": score.item()
        })

    retrieved = [m for m in retrieved if m["score"] > MIN_SCORE]
    retrieved.sort(key=lambda m: m["timestamp"])  # chronological order
    return retrieved


def build_prompt(query, retrieved, is_summary=False):
    context_lines = [
        f"- {humanize_timestamp(m['timestamp'])}, saw: {m['caption']}"
        for m in retrieved
    ]
    context = "\n".join(context_lines)

    pov_rules = """POV rules:
- If a memory describes hands, an object being held, or a close-up view (like "hands holding a cup"), that is the user's OWN point of view — describe it as "you were holding/using..." (first person, direct).
- If a memory describes a full person (like "a person sitting on a couch" or "a man standing near a door"), that is someone ELSE the camera saw, not the user — describe it as "you saw someone..." (third person, about another person).
- Never refer to the user themselves as "someone" or "the person" — the user is always "you"."""

    if is_summary:
        return f"""You are Cortex, a personal memory assistant speaking directly to the user.

The user asked a broad question about their whole day. Below is every memory captured today, in chronological order.

{pov_rules}

Rules:
- Go through the memories in order and mention the key distinct moments factually.
- Do NOT invent a narrative, feelings, transitions, or events that aren't directly written in the memories.
- If two memories are basically the same thing, don't repeat it, just mention it once.
- Keep it to a short list-like summary, a few sentences, not a story.

Today's memories:
{context}

Question: {query}

Answer:"""

    return f"""You are Cortex, a personal memory assistant speaking directly to the user.

The memories below are listed in the exact order they happened, in the format "time, saw: description". These are the memories judged most relevant to the question — they may not perfectly answer it.

{pov_rules}

Rules:
- Only state what is directly written in the memories below. Do not infer purpose, plans, or context that isn't explicitly there.
- Do not invent objects, actions, locations, or events not word-for-word supported by the memories.
- If you are not confident these memories actually answer the question, say so honestly, then just list the key related memories with their times instead of guessing.
- You may connect memories into a simple sequence only if directly supported.
- Keep the answer short and direct — 1-3 sentences, or a short list if listing memories.

Memories:
{context}

Question: {query}

Answer:"""


def generate_answer(prompt):
    response = ollama.generate(
        model="llama3.2",
        prompt=prompt,
        options={"temperature": 0.1}
    )
    return response["response"].strip()


def run_query_loop():
    embed_model = load_models()
    memory_log = load_memory_log()
    captions = [entry["caption"] for entry in memory_log]
    caption_embeddings = embed_model.encode(captions, convert_to_tensor=True)

    print(f"\nCortex is ready. {len(memory_log)} memories loaded. Ask me anything (type 'exit' to quit).\n")

    while True:
        query = input("You: ")
        if query.lower() == "exit":
            break

        if is_summary_question(query):
            todays = get_todays_memories(memory_log)
            if not todays:
                print("\nCortex: I don't have any memories from today.\n")
                continue
            prompt = build_prompt(query, todays, is_summary=True)
        else:
            retrieved = retrieve_memories(query, memory_log, embed_model, caption_embeddings)
            if not retrieved:
                print("\nCortex: I don't have any memory related to that.\n")
                continue
            prompt = build_prompt(query, retrieved, is_summary=False)

        answer = generate_answer(prompt)
        print(f"\nCortex: {answer}\n")


if __name__ == "__main__":
    run_query_loop()