# Cortex: Wearable Edge-AI Local Memory Assistant

Cortex is an ultra-low-latency, privacy-focused wearable AI assistant designed to operate fully on local edge hardware, such as the Raspberry Pi 5. By combining automated real-time visual captioning with local vector retrieval and lightweight large language models, Cortex continuously captures, indexes, and queries daily experiences using natural language without relying on external cloud APIs or third-party web services.

---

## Technical Overview

The platform operates across a three-layer modular architecture hosted entirely on the Raspberry Pi 5:

1. **Vision Capture Layer:** Captures periodic image frames via connected USB video devices or remote wireless hardware nodes and passes them to a local BLIP image captioning model.
2. **Embedding and Vector Store Engine:** Converts natural language captions into 384-dimensional dense vector embeddings via SentenceTransformers (`all-MiniLM-L6-v2`) and performs cosine similarity matching against locally stored memory logs (`memory_log.json`).
3. **Local In-Context Inference:** Constructs structured, zero-hallucination Retrieval-Augmented Generation (RAG) prompts and passes relevant memory context to a local Ollama instance running `llama3.2:1b`.
4. **Client Interface:** Serves an interactive React/Vite dashboard accessible over the local network for querying, adding notes, and reviewing indexed memories.

---

## Hardware and Software Specifications

### Hardware
* Primary Processor: Raspberry Pi 5 (8GB RAM recommended)
* Camera Capture Node: USB Webcam (`/dev/video0`) or ESP32-CAM wireless module

### Software Dependencies
* Operating System: Raspberry Pi OS (macOS/Linux compatible for local development)
* Language Runtime: Python 3.13
* Deep Learning Frameworks: PyTorch, Hugging Face Transformers
* Machine Learning Models:
  * Vision: `Salesforce/blip-image-captioning-base`
  * Text Embeddings: `sentence-transformers/all-MiniLM-L6-v2`
  * Language Model: Ollama running `llama3.2:1b`
* Backend Service: Flask, Flask-CORS
* Frontend Interface: React, Vite, Tailwind CSS

---

## Quick Start and Local Development

### 1. Repository Setup and Environment
Clone the repository and initialize a Python virtual environment:

```bash
git clone [https://github.com/Tanish225/cortex.git](https://github.com/Tanish225/cortex.git)
cd cortex
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
Local Language Model Setup
Ensure Ollama is installed on your host system and pull the target 1B parameter model:
```bash
curl -fsSL [https://ollama.com/install.sh](https://ollama.com/install.sh) | sh
ollama pull llama3.2:1b
```

Manual Server Execution
To run the service components individually during development:
Backend (Port 5001)
```bash
source venv/bin/activate
cd backend
python3 app.py
```

Frontend (Port 5173)
```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

System Automation and Deployment
To support headless operation on boot, Cortex utilizes systemd to orchestrate service preloading, model weight initialization, and background capture loops.

Automation Script (~/start_cortex.sh)
```bash
#!/bin/bash

# 1. Start Flask Backend
cd /home/cortex/cortex/backend
source ../venv/bin/activate
export DEFAULT_USERNAME="tanish"
python3 app.py &

# Allow Flask to initialize model weights in RAM
echo "Waiting for Flask AI models to initialize..."
sleep 15

# 2. Start Frontend UI (Vite)
cd /home/cortex/cortex/frontend
npm run dev -- --host 0.0.0.0 &

# 3. Start Live Capture Loop
cd /home/cortex/cortex/backend
python3 live_capture.py &

wait
```

System Service Configuration
(/etc/systemd/system/cortex.service)
```bash
[Unit]
Description=Cortex Wearable Edge-AI Assistant Service
After=network.target ollama.service

[Service]
Type=simple
User=cortex
WorkingDirectory=/home/cortex
ExecStart=/home/cortex/start_cortex.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```
To enable autonomous startup on boot:
```bash
sudo systemctl daemon-reload
sudo systemctl enable ollama
sudo systemctl enable cortex.service
sudo systemctl start cortex.service
```

In-Context Safety Rules
Cortex enforces strict prompting constraints within build_prompt_data() to guarantee factual integrity:
In-Context Verification: The model is restricted to generating answers strictly from factual data present in the <memories> context block.
Default Fallback: If a query cannot be answered using indexed memories or temporal context, the system returns: "I don't have any information about that."
Temporal Grounding: Real-time system clocks are injected into the prompt context to resolve relative queries regarding dates and times accurately.



