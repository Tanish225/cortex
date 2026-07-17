import cv2
import json
import os
import time
from datetime import datetime
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration

print("Loading captioning model...")
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

CAPTURE_INTERVAL = 5  # seconds between captures — change this if you want faster/slower
LOG_FILE = "memory_log.json"
PHOTOS_DIR = "live_photos"

os.makedirs(PHOTOS_DIR, exist_ok=True)

# Load existing memory log if it exists, so we keep adding instead of overwriting
if os.path.exists(LOG_FILE):
    with open(LOG_FILE, "r") as f:
        memory_log = json.load(f)
else:
    memory_log = []

cap = cv2.VideoCapture(0)  # 0 = default Mac webcam

if not cap.isOpened():
    print("Could not access the webcam. Check System Settings > Privacy > Camera permissions for Terminal/VS Code.")
    exit()

print(f"\nLive capture started. Taking a photo every {CAPTURE_INTERVAL} seconds.")
print("Press Ctrl+C to stop.\n")

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame, retrying...")
            time.sleep(1)
            continue

        timestamp = datetime.now()
        filename = f"frame_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
        filepath = os.path.join(PHOTOS_DIR, filename)
        cv2.imwrite(filepath, frame)

        # Convert BGR (OpenCV) to RGB (PIL) for the captioning model
        image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        inputs = processor(image, return_tensors="pt")
        output = model.generate(**inputs, max_new_tokens=30)
        caption = processor.decode(output[0], skip_special_tokens=True)

        print(f"[{timestamp.strftime('%H:%M:%S')}] {caption}")

        memory_log.append({
            "filename": filename,
            "caption": caption,
            "timestamp": timestamp.isoformat()
        })

        with open(LOG_FILE, "w") as f:
            json.dump(memory_log, f, indent=2)

        time.sleep(CAPTURE_INTERVAL)

except KeyboardInterrupt:
    print("\n\nStopped live capture. Releasing camera.")
    cap.release()