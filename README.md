Markdown
# Cortex: Wearable Edge-AI External Memory Prosthesis for Alzheimer's Care

Cortex is a wearable external memory prosthesis designed to assist individuals living with early-to-moderate Alzheimer's disease and episodic memory loss. The system passively records daily events as descriptive text captions, vectorizes them locally, and allows the wearer or a caregiver to ask plain-language questions via a voice/text interface using Retrieval-Augmented Generation (RAG).

Built on a **Raspberry Pi 5**, Cortex enforces a strict **zero-frame transmission trust boundary**: raw camera images never leave the board. Only text records (caption, timestamp, and dense embedding) cross over to the local or managed backend, reducing data bandwidth by 372x and preserving bystander privacy.

---

## Technical Architecture

The Cortex architecture splits execution across an on-board edge capture pipeline and a Retrieval-Augmented Generation (RAG) backend:

| System Layer | Pipeline Stage | Operational Details |
| :--- | :--- | :--- |
| **Wearable Edge Node**<br>*(Raspberry Pi 5)* | **Camera Module** | Captures image frame (stored strictly in local RAM) |
| | **BLIP Captioning** | Generates descriptive text caption from frame |
| | **MiniLM Embedding** | Encodes caption into a 384-dimensional dense vector |
| | **Cosine Duplicate Check** | Drops record if similarity $\cos(e_t, e_{t-1}) > 0.9$ |
| **=== TRUST BOUNDARY ===** | **Data Transmission** | **Only JSON payload `{caption, timestamp, vector}` leaves board** |
| **Managed Backend** | **Ingest Service** | Receives structured text + vector payloads |
| | **Memory Store** | Caches text captions and dense embeddings |
| | **RAG Pipeline + Llama 3** | Performs cosine retrieval and generates grounded answers |
| | **User App Interface** | Handles voice/text queries for wearer and caregiver |

### 1. On-Board Capture & Edge Processing
* **Automated Cycle ($T = 10\text{ s}$):** An OS service starts on boot without user intervention. Every 10 seconds, it grabs a camera frame, captions it using BLIP, and encodes the text into a 384-dimensional vector using `all-MiniLM-L6-v2`.
* **Cosine Duplicate Filtering:** To conserve storage and eliminate static frames (e.g., sitting at a desk), a new caption vector $e_t$ is dropped if its cosine similarity to the previous frame $e_{t-1}$ exceeds $\theta = 0.9$:
  $$\cos(e_t, e_{t-1}) > 0.9$$
* **Trust Boundary Enforcement:** Raw JPEG images ($\sim 1,521\text{ KB}$) stay strictly in RAM on the Pi 5. Only lightweight JSON text records ($\sim 4,088\text{ bytes}$) leave the board.

### 2. Retrieval-Augmented Generation (RAG)
* **Vector Storage:** Memories are stored as $(c, t, e)$ triples representing caption, ISO timestamp, and embedding vector.
* **Linear Scan Search:** Questions are embedded using MiniLM. A cosine scan extracts the top $k = 5$ candidate memories with a similarity score $\ge 0.15$. Candidates are sorted chronologically before prompt injection to preserve episodic sequence.
* **In-Context Grounding:** Llama 3 generates responses based strictly on retrieved facts. If a query is unanswerable from the context, the model falls back to `"I don't have any information about that."`

---

## Performance Benchmarks & Experimental Results

Cortex was evaluated on the Raspberry Pi 5 platform using BLIP-base and `all-MiniLM-L6-v2` under a $10\text{ s}$ duty cycle.

### Hardware Execution Profile ($T = 10\text{ s}$)

| Execution Stage / Metric | Value |
| :--- | :--- |
| **CPU / Microarchitecture** | $4\times$ Cortex-A76 @ 2.4 GHz |
| **Hardware Accelerator** | None (ARM Neon CPU) |
| **Camera Acquisition Time** | $31.4\text{ ms}$ |
| **BLIP Captioning Latency** | $5.92\text{ s}$ |
| **MiniLM Embedding Latency** | $518.2\text{ ms}$ |
| **Record Build Time** | $2.1\text{ ms}$ |
| **Total Cycle Time ($T_{\text{cycle}}$)** | **$6.54\text{ s}$** |
| **Real-Time Margin ($M = 10\text{s} - T_{\text{cycle}}$)** | **$3.46\text{ s}$** |
| **Peak Resident Memory** | $2,850\text{ MB}$ |
| **Mean CPU Load** | $74.2\%$ |
| **Max Temperature (30-min Soak Test)** | **$58.1^\circ\text{C}$ (0 overruns)** |

### System Efficiency & Readability Metrics

| Metric Category | Performance Indicator | Value |
| :--- | :--- | :--- |
| **Data Compression** | Compression Ratio ($\rho$) | $372\times$ reduction per frame |
| **Bandwidth** | 24-Hour Network Usage | **$35.32\text{ MB/day}$** (vs $7.96\text{ GB/day}$ raw video) |
| **Retrieval Latency** | $N = 1,000$ Memories | $0.14\text{ ms}$ |
| **Retrieval Latency** | $N = 10,000$ Memories | $1.25\text{ ms}$ ($0.03\%$ of one BLIP step) |
| **Retrieval Accuracy** | Acc@1 | $84.0\%$ |
| **Retrieval Accuracy** | Acc@3 | $96.0\%$ |
| **Retrieval Quality** | Mean Reciprocal Rank (MRR) | $0.89$ |
| **Readability** | Flesch Reading Ease | $61.5 \rightarrow$ **$84.2$** (Support Mode) |
| **Readability** | Average Sentence Length | $16.2 \rightarrow$ **$10.1$ words** |
| **Readability** | Absolute Timestamps per Answer | $1.4 \rightarrow$ **$0.0$** (Relative time mapping) |

---

## Care-Focused Support Mode

Cortex includes an accessibility configuration tailored for Alzheimer's patients based on grammatical complexity studies:

| Query Type | Input / Mode | System Output |
| :--- | :--- | :--- |
| **User Query** | **Question** | *"Where is my laptop?"* |
| **Standard Mode** | **Detailed Response** | *"You left your laptop on the wooden desk at 2:15 PM today."* |
| **Support Mode** | **Simplified Response** | *"Your laptop is on your desk."* |

### Support Mode Adaptations
1. **Syntax Simplification:** Sentences are capped at $\sim 10$ words.
2. **Relative Time Mapping:** Absolute timestamps ("2:15 PM") are converted into natural relative phrases ("earlier today").
3. **Calm Tone & Direct Fact Reporting:** Language never implies the user ought to have remembered.
4. **Speech Rate:** Synthesized voice output is slowed to $0.8\times$ speed for lower auditory processing strain.

---

## Software & Hardware Specifications

### Hardware Platform
* **Board:** Raspberry Pi 5 (8GB LPDDR4X RAM recommended)
* **Camera:** Sony IMX708 Camera Module connected via CSI ribbon cable
* **Power Supply:** USB-C PD (5V / 5A)

### Software Stack
* **OS:** Raspberry Pi OS (Bookworm, 64-bit)
* **Environment:** Python 3.11+
* **Inference Libraries:** PyTorch (CPU Neon optimizations), Hugging Face Transformers, SentenceTransformers
* **Backend Framework:** Flask, Flask-CORS
* **LLM Engine:** Ollama running `llama3.2:1b` (or Llama 3 RAG service)
* **Frontend:** React, Vite, Tailwind CSS

  ---

## Quick Start & Installation

### 1. Repository Setup
```bash
git clone [https://github.com/Tanish225/cortex.git](https://github.com/Tanish225/cortex.git)
cd cortex
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
2. Ollama Installation & Model Pull
```Bash
curl -fsSL [https://ollama.com/install.sh](https://ollama.com/install.sh) | sh
ollama pull llama3.2:1b
```
3. Manual Server Execution
Backend (Port 5001):
```Bash
source venv/bin/activate
cd backend
python3 app.py
```
Frontend (Port 5173):
```Bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```
System Automation & Deployment
For unattended operation on boot, Cortex uses a systemd service script.   

1. Automation Startup Script (~/start_cortex.sh)
```Bash
#!/bin/bash

# 1. Start Flask Backend
cd /home/cortex/cortex/backend
source ../venv/bin/activate
export DEFAULT_USERNAME="tanish"
python3 app.py &

# Allow PyTorch & HuggingFace models to preload into RAM
echo "Waiting for Flask AI models to initialize..."
sleep 15

# 2. Start Frontend UI (Vite)
cd /home/cortex/cortex/frontend
npm run dev -- --host 0.0.0.0 &

# 3. Start On-Board Capture Loop
cd /home/cortex/cortex/backend
python3 live_capture.py &

wait
```
Make the script executable:
```Bash
chmod +x ~/start_cortex.sh
```
2. Systemd Service Configuration (/etc/systemd/system/cortex.service)
```Ini, TOML
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
Enable and start the background service:
```Bash
sudo systemctl daemon-reload
sudo systemctl enable ollama
sudo systemctl enable cortex.service
sudo systemctl start cortex.service
```
