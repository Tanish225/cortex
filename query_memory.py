import json
from sentence_transformers import SentenceTransformer, util


print("Loading search model...")
local_path = r"/Users/tanishsinha/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
model = SentenceTransformer(local_path)

with open("memory_log.json", "r") as f:
    memory_log = json.load(f)

captions = [entry["caption"] for entry in memory_log]
caption_embeddings = model.encode(captions, convert_to_tensor=True)

print("\nYour memory log is loaded. Ask me anything (type 'exit' to quit).\n")

while True:
    query = input("You: ")
    if query.lower() == "exit":
        break

    query_embedding = model.encode(query, convert_to_tensor=True)
    scores = util.cos_sim(query_embedding, caption_embeddings)[0]

    best_idx = scores.argmax().item()
    best_score = scores[best_idx].item()
    best_match = memory_log[best_idx]


    if best_score < 0.25:
        print(f"\n  Hmm, I don't have a confident memory matching that. (closest guess: \"{best_match['caption']}\", confidence {best_score:.2f})\n")
    else:
        print(f"\n  Best match: \"{best_match['caption']}\"")
        print(f"  Photo: {best_match['filename']}")
        print(f"  Time: {best_match['timestamp']}")
        print(f"  Confidence: {best_score:.2f}\n")