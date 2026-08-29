import os
import cv2
import json
from datetime import datetime
from PIL import Image

# Setup exact relative path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "memory_log.json")

def capture_and_process(username, embed_model, vision_processor, vision_model):
    print("Capturing frame...")
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print("Failed to grab frame.")
        return None

    # Convert directly to PIL Image in RAM (No saving to disk!)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(rgb_frame)

    print("Generating caption with AI...")
    # Process the image through the vision model
    inputs = vision_processor(image, return_tensors="pt")
    out = vision_model.generate(**inputs)
    caption = vision_processor.decode(out[0], skip_special_tokens=True)
    
    print(f"AI saw: {caption}")

    print("Generating embedding...")
    embedding = embed_model.encode(caption).tolist()
    
    # Exactly matching the memory_log.json schema
    new_memory = {
        "filename": f"memory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg",
        "caption": caption,
        "timestamp": datetime.now().isoformat(),
        "embedding": embedding,
        "owner": username,
        "source": "live_capture"
    }

    # Append to memory log
    try:
        with open(LOG_FILE, "r") as f:
            memories = json.load(f)
    except FileNotFoundError:
        memories = []

    memories.append(new_memory)

    with open(LOG_FILE, "w") as f:
        json.dump(memories, f, indent=2)

    print("Memory saved successfully without storing the photo!")
    return new_memory