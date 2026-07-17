import json
import ollama
from datetime import datetime
from sentence_transformers import SentenceTransformer, util

print("Loading search model...")
local_path = r"/Users/tanishsinha/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
model = SentenceTransformer(local_path)

with open("memory_log.json", "r") as f:
    memory_log = json.load(f)

captions = [entry["caption"] for entry in memory_log]
caption_embeddings = model.encode(captions, convert_to_tensor=True)

TOP_K = 5          # slightly higher, gives more surrounding context to reason with
MIN_SCORE = 0.15


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


print("\nCortex is ready. Ask me anything (type 'exit' to quit).\n")

while True:
    query = input("You: ")
    if query.lower() == "exit":
        break

    query_embedding = model.encode(query, convert_to_tensor=True)
    scores = util.cos_sim(query_embedding, caption_embeddings)[0]

    top_results = scores.topk(min(TOP_K, len(captions)))

    retrieved = []
    for score, idx in zip(top_results.values, top_results.indices):
        idx = idx.item()
        retrieved.append({
            "caption": memory_log[idx]["caption"],
            "timestamp": memory_log[idx]["timestamp"],
            "score": score.item()
        })

    retrieved = [m for m in retrieved if m["score"] > MIN_SCORE]

    if not retrieved:
        print("\nCortex: I don't have any memory related to that.\n")
        continue

    # Sort chronologically so the LLM can see the actual sequence of events
    retrieved.sort(key=lambda m: m["timestamp"])

    context_lines = [
        f"- {humanize_timestamp(m['timestamp'])}, saw: {m['caption']}"
        for m in retrieved
    ]
    context = "\n".join(context_lines)

    prompt = f"""You are Cortex, a personal memory assistant. The user's memories below are listed in the exact order they happened. Use them to answer the user's question in natural sentences.

You may connect the memories together to describe a sequence of events (e.g. "you got coffee, then went back to your desk"), but only if that sequence is clearly supported by the memories given. Use the exact times given. Do not invent actions, objects, or details that aren't in the memories below. If your user, greets you... greet them back, keep the conversation clear. conversate from the user.

Memories:
{context}

Question: {query}

Answer:"""

    response = ollama.generate(model="llama3.2", prompt=prompt)

    print(f"\nCortex: {response['response'].strip()}\n")