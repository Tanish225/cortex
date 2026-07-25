import cv2
import json
import os
import time
from datetime import datetime
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration
from sentence_transformers import SentenceTransformer, util

CAPTURE_INTERVAL = 5          # seconds between captures
LOG_FILE = "memory_log.json"
PHOTOS_DIR = "live_photos"
DUPLICATE_THRESHOLD = 0.9     # if new caption is this similar to the last one, skip saving it


def load_models():
    print("Loading captioning model...")
    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    caption_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

    print("Loading embedding model...")
    embed_model = SentenceTransformer("all-MiniLM-L6-v2")

    return processor, caption_model, embed_model


def load_memory_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    return []


def save_memory_log(memory_log):
    with open(LOG_FILE, "w") as f:
        json.dump(memory_log, f, indent=2)


def capture_frame(cap):
    """Grabs a single frame from the webcam. Returns the raw frame or None."""
    ret, frame = cap.read()
    if not ret:
        return None
    return frame


def generate_caption(frame, processor, caption_model):
    """Converts a raw camera frame into a text caption."""
    image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    inputs = processor(image, return_tensors="pt")
    output = caption_model.generate(**inputs, max_new_tokens=30)
    return processor.decode(output[0], skip_special_tokens=True)


def is_duplicate(new_caption, last_caption, embed_model):
    """Checks if new_caption is basically the same memory as the last one saved."""
    if last_caption is None:
        return False
    embeddings = embed_model.encode([new_caption, last_caption], convert_to_tensor=True)
    similarity = util.cos_sim(embeddings[0], embeddings[1]).item()
    return similarity > DUPLICATE_THRESHOLD


def save_frame_to_disk(frame, timestamp):
    filename = f"frame_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
    filepath = os.path.join(PHOTOS_DIR, filename)
    cv2.imwrite(filepath, frame)
    return filename


def run_live_capture():
    os.makedirs(PHOTOS_DIR, exist_ok=True)
    processor, caption_model, embed_model = load_models()
    memory_log = load_memory_log()
    last_caption = memory_log[-1]["caption"] if memory_log else None

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Could not access the webcam. Check camera permissions.")
        return

    print(f"\nLive capture started. Checking every {CAPTURE_INTERVAL} seconds.")
    print(f"Memories so far: {len(memory_log)}")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            frame = capture_frame(cap)
            if frame is None:
                print("Failed to grab frame, retrying...")
                time.sleep(1)
                continue

            timestamp = datetime.now()
            caption = generate_caption(frame, processor, caption_model)

            if is_duplicate(caption, last_caption, embed_model):
                print(f"[{timestamp.strftime('%H:%M:%S')}] (skipped, same as last) {caption}")
                time.sleep(CAPTURE_INTERVAL)
                continue

            filename = save_frame_to_disk(frame, timestamp)

            # Compute the embedding once, right now, and store it — so the backend
            # never has to re-embed this caption again on every future query.
            embedding = embed_model.encode(caption).tolist()

            memory_log.append({
                "filename": filename,
                "caption": caption,
                "timestamp": timestamp.isoformat(),
                "embedding": embedding
            })
            save_memory_log(memory_log)
            last_caption = caption

            print(f"[{timestamp.strftime('%H:%M:%S')}] SAVED: {caption}  (total memories: {len(memory_log)})")
            time.sleep(CAPTURE_INTERVAL)

    except KeyboardInterrupt:
        print(f"\n\nStopped. Total memories saved: {len(memory_log)}")
        cap.release()


if __name__ == "__main__":
    run_live_capture()
