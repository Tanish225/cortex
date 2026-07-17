# Cortex

**Chat With Your Memories.**

Cortex is a personal memory assistant. A camera captures moments throughout your day, an AI describes each one in a short caption, and you can later ask natural English questions like *"where did I leave my keys"* to recall it, all without ever storing or sending raw images anywhere.

## How it works

1. **Capture** — a camera (a wearable camera on a NXP board) grabs a frame every few seconds
2. **Caption** — a vision-language AI model (BLIP) converts the frame into a short text description
3. **Store** — the caption + timestamp gets saved (duplicate/near-identical moments are automatically skipped)
4. **Retrieve** — when you ask a question, it's converted into a vector and compared against all stored memories using cosine similarity, to find the closest match
5. **Generate** — the top matching memories are handed to a local LLM (Llama 3.2 via Ollama), which writes a natural, direct answer

This is a full **RAG (Retrieval-Augmented Generation)** pipeline, currently running entirely locally as a proof of concept.

## Why this is novel

- **Privacy-first** — only text descriptions are ever stored, never raw images/video
- **On-device filtering (planned)** — hardware-accelerated motion/scene-change detection means the device only processes frames when something actually changed, saving power
- The combination of privacy-preserving text-only memory + personal episodic retrieval is what makes this different from existing smart glasses products

## Tech stack

| Component | Tool | Purpose |
|---|---|---|
| Camera capture | OpenCV | Grabs frames from the camera |
| Captioning | BLIP (Salesforce, via Hugging Face) | Describes each frame in a sentence |
| Retrieval | Sentence-Transformers (`all-MiniLM-L6-v2`) | Converts text to embeddings, finds relevant memories via cosine similarity |
| Generation | Llama 3.2 (via Ollama) | Generates natural-language answers grounded in retrieved memories |
| Planned hardware | PYNQ-Z2 or NXP i.MX board | Standalone wearable capture + on-device processing |
| Planned cloud | AWS (IoT Core, Lambda, DynamoDB) | Standalone operation without a laptop |

## Project structure

```
cortex/
├── live_capture.py       # Captures frames from webcam, generates captions, saves to memory log
├── query_memory_rag.py   # Query interface — ask questions, get RAG-generated answers
├── memory_log.json        # Stored memories (gitignored — personal data)
├── photos/ / live_photos/ # Captured images (gitignored — personal data)
└── .gitignore
```

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install torch transformers pillow sentence-transformers numpy opencv-python ollama
```

Also install [Ollama](https://ollama.com) and pull the model:
```bash
ollama pull llama3.2
```

## Usage

**1. Capture memories (run this while going about your day/testing):**
```bash
python live_capture.py
```
Press `Ctrl+C` to stop.

**2. Ask questions about your memories:**
```bash
python query_memory_rag.py
```
Type your question, or `exit` to quit.

## Team

Built as a cloud computing course project.
