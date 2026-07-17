import os
import json
from datetime import datetime
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration

print("Loading captioning model... (first run will download ~1GB, be patient)")

processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

photos_folder = "photos"
memory_log = []

for filename in os.listdir(photos_folder):
    if not filename.lower().endswith((".jpg", ".jpeg", ".png", ".heic")):
        continue

    filepath = os.path.join(photos_folder, filename)
    print(f"Processing {filename}...")

    try:
        image = Image.open(filepath).convert("RGB")
    except Exception as e:
        print(f"  Skipping {filename}, couldn't open: {e}")
        continue

    inputs = processor(image, return_tensors="pt")
    output = model.generate(**inputs, max_new_tokens=30)
    caption = processor.decode(output[0], skip_special_tokens=True)

    print(f"  Caption: {caption}")

    memory_log.append({
        "filename": filename,
        "caption": caption,
        "timestamp": datetime.now().isoformat()
    })

with open("memory_log.json", "w") as f:
    json.dump(memory_log, f, indent=2)

print(f"\nDone! Captioned {len(memory_log)} photos. Saved to memory_log.json")