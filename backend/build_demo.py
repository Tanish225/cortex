import os
import json
from datetime import datetime
from sentence_transformers import SentenceTransformer

# 1. Ask the user for their username dynamically
YOUR_USERNAME = input("Enter your Cortex username (the one you log in with): ").strip()

if not YOUR_USERNAME:
    print("Username cannot be blank. Exiting.")
    exit()

# 2. Automatically find memory_log.json in the exact same folder as this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(BASE_DIR, "memory_log.json")

print("Loading AI embedding model...")
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

print(f"Reading {FILE_PATH}...")
try:
    with open(FILE_PATH, "r") as f:
        memories = json.load(f)
except FileNotFoundError:
    print(f"Could not find memory_log.json in {BASE_DIR}. Check if the file is there!")
    exit()

print("Generating embeddings, fixing tags, and syncing timestamps to TODAY...")
# Get today's dynamic date
today_str = datetime.now().strftime('%Y-%m-%d')

for m in memories:
    # Force the owner to match the provided login so they aren't hidden
    m["owner"] = YOUR_USERNAME
    if "source" not in m:
        m["source"] = "capture"
        
    # THE TIME TRAVEL FIX: Force all memory dates to be "today" while keeping the time
    if "timestamp" in m:
        time_part = m["timestamp"].split("T")[1] if "T" in m["timestamp"] else m["timestamp"]
        m["timestamp"] = f"{today_str}T{time_part}"
        
    # Generate the missing vector arrays
    m["embedding"] = embed_model.encode(m["caption"]).tolist()

with open(FILE_PATH, "w") as f:
    json.dump(memories, f, indent=2)

print(f" demo file is now fully embedded, time-synced to today, and tagged to '{YOUR_USERNAME}'.")