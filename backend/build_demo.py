import json
from sentence_transformers import SentenceTransformer

# Hardcoded to match your users.json exactly
YOUR_USERNAME = "tanishsinha"

# Using the exact absolute path to prevent duplicate files
FILE_PATH = "/Users/tanishsinha/second-brain-poc/second-brain-poc/backend/memory_log.json"

print("Loading AI embedding model...")
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

print(f"Reading {FILE_PATH}...")
try:
    with open(FILE_PATH, "r") as f:
        memories = json.load(f)
except FileNotFoundError:
    print(f"Could not find {FILE_PATH}. Check if the file is there!")
    exit()

print("Generating embeddings and fixing tags...")
for m in memories:
    # Force the owner to match your exact login so they aren't hidden
    m["owner"] = YOUR_USERNAME
    if "source" not in m:
        m["source"] = "capture"
        
    # Generate the missing vector arrays
    m["embedding"] = embed_model.encode(m["caption"]).tolist()

with open(FILE_PATH, "w") as f:
    json.dump(memories, f, indent=2)

print("Done! Your demo file is now fully embedded and ready to present.")