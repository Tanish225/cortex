import json
import ollama
from datetime import datetime
from sentence_transformers import SentenceTransformer, util

LOG_FILE = "memory_log.json"
TOP_K = 5
MIN_SCORE = 0.15


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


def build_prompt(query, retrieved):
    context_lines = [
        f"- {humanize_timestamp(m['timestamp'])}, saw: {m['caption']}"
        for m in retrieved
    ]
    context = "\n".join(context_lines)

    return f"""You are Cortex, a personal memory assistant. The memories below are listed in the exact order they happened. Use them to answer the user's question in 1-2 short, natural sentences.

You may connect memories together to describe a sequence of events, but only if that sequence is clearly supported by the memories given. Use the exact times given. Do not invent actions, objects, or details that aren't in the memories below.

Memories:
{context}

Question: {query}

Answer:"""


def generate_answer(prompt):
    response = ollama.generate(model="llama3.2", prompt=prompt)
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

        retrieved = retrieve_memories(query, memory_log, embed_model, caption_embeddings)

        if not retrieved:
            print("\nCortex: I don't have any memory related to that.\n")
            continue

        prompt = build_prompt(query, retrieved)
        answer = generate_answer(prompt)
        print(f"\nCortex: {answer}\n")


if __name__ == "__main__":
    run_query_loop()