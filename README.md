Markdown
# Cortex: Wearable Edge-AI External Memory Prosthesis for Alzheimer's Care

Cortex is a wearable external memory prosthesis designed to assist individuals living with early-to-moderate Alzheimer's disease and episodic memory loss. The system passively records daily events as descriptive text captions, vectorizes them locally, and allows the wearer or a caregiver to ask plain-language questions via a voice/text interface using Retrieval-Augmented Generation (RAG)[cite: 4].

Built on a **Raspberry Pi 5**, Cortex enforces a strict **zero-frame transmission trust boundary**: raw camera images never leave the board[cite: 4, 5]. Only text records (caption, timestamp, and dense embedding) cross over to the local or managed backend, reducing data bandwidth by 372x and preserving bystander privacy[cite: 4, 8].

---

## Technical Architecture

The Cortex architecture splits execution across an on-board edge capture pipeline and a Retrieval-Augmented Generation (RAG) backend[cite: 5]:

+-----------------------------------------------------------------------------------+
|                        WEARABLE EDGE NODE (Raspberry Pi 5)                        |
|                                                                                   |
|  [ Camera Module ] ---> [ BLIP Captioning ] ---> [ MiniLM Embedding ]              |
|        │                        │                         │                       |
|  (Frames local)         (Text Caption)             (384d Vector)                  |
|                                                           │                       |
|                                                 [ Cosine Duplicate Check ]        |
|                                                           │ (cos <= 0.9)          |
+-----------------------------------------------------------┼-----------------------+
│
=== TRUST BOUNDARY ===                 │ {caption, time, vector}
▼
+-----------------------------------------------------------------------------------+
|                                 MANAGED BACKEND                                   |
|                                                                                   |
|    [ Ingest Service ] ---> [ Memory Store ] <---> [ RAG Pipeline + Llama 3 ]      |
|                                                                 ▲                 |
+-----------------------------------------------------------------┼-----------------+
│
[ User App (Voice/Text) ]

### 1. On-Board Capture & Edge Processing
* **Automated Cycle ($T = 10\text{ s}$):** An OS service starts on boot without user intervention[cite: 5, 6]. Every 10 seconds, it grabs a camera frame, captions it using BLIP, and encodes the text into a 384-dimensional vector using `all-MiniLM-L6-v2`[cite: 5].
* **Cosine Duplicate Filtering:** To conserve storage and eliminate static frames (e.g., sitting at a desk), a new caption vector $e_t$ is dropped if its cosine similarity to the previous frame $e_{t-1}$ exceeds $\theta = 0.9$[cite: 5]:
  $$\cos(e_t, e_{t-1}) > 0.9$$
* **Trust Boundary Enforcement:** Raw JPEG images ($\sim 1,521\text{ KB}$) stay strictly in RAM on the Pi 5[cite: 4, 8]. Only lightweight JSON text records ($\sim 4,088\text{ bytes}$) leave the board[cite: 4, 8].

### 2. Retrieval-Augmented Generation (RAG)
* **Vector Storage:** Memories are stored as $(c, t, e)$ triples representing caption, ISO timestamp, and embedding vector[cite: 6].
* **Linear Scan Search:** Questions are embedded using MiniLM[cite: 6]. A cosine scan extracts the top $k = 5$ candidate memories with a similarity score $\ge 0.15$[cite: 6]. Candidates are sorted chronologically before prompt injection to preserve episodic sequence[cite: 6].
* **In-Context Grounding:** Llama 3 generates responses based strictly on retrieved facts[cite: 6]. If a query is unanswerable from the context, the model falls back to `"I don't have any information about that."`

---

## Performance Benchmarks & Experimental Results

Cortex was tested across two edge hardware platforms using identical code, models (BLIP-base and `all-MiniLM-L6-v2`), and a $10\text{ s}$ duty cycle[cite: 4, 6].

### Hardware Execution Comparison ($T = 10\text{ s}$)

| Metric | Nvidia Jetson Nano (CUDA) | Raspberry Pi 5 (CPU / Neon) | Performance Delta |
| :--- | :--- | :--- | :--- |
| **CPU / Microarchitecture** | $4\times$ Cortex-A57 @ 1.43 GHz[cite: 6] | $4\times$ Cortex-A76 @ 2.4 GHz[cite: 6] | Upgraded Core Arch[cite: 6, 7] |
| **Accelerator** | 128-core Maxwell GPU[cite: 6] | None (ARM Neon CPU)[cite: 6] | CPU-Optimized[cite: 6, 7] |
| **Camera Acquisition Time** | $42.1\text{ ms}$[cite: 7] | $31.4\text{ ms}$[cite: 7] | 25% faster[cite: 7] |
| **BLIP Captioning Latency** | $8.75\text{ s}$[cite: 7] | $5.92\text{ s}$[cite: 7] | 32% faster[cite: 7] |
| **MiniLM Embedding Latency**| $712.4\text{ ms}$[cite: 7] | $518.2\text{ ms}$[cite: 7] | 27% faster[cite: 7] |
| **Record Build Time** | $3.2\text{ ms}$[cite: 7] | $2.1\text{ ms}$[cite: 7] | 34% faster[cite: 7] |
| **Total Cycle Time ($T_{\text{cycle}}$)** | **$9.53\text{ s}$**[cite: 4, 7] | **$6.54\text{ s}$**[cite: 4, 7] | **31% faster overall**[cite: 4, 7] |
| **Real-Time Margin ($M = 10\text{s} - T_{\text{cycle}}$)** | $0.47\text{ s}$[cite: 7] | **$3.46\text{ s}$**[cite: 4, 7] | **$7.36\times$ wider margin**[cite: 4, 7] |
| **Peak Resident Memory** | $3,420\text{ MB}$[cite: 7] | $2,850\text{ MB}$[cite: 7] | 16.6% lower RAM footprint[cite: 7] |
| **Mean CPU Load** | $88.4\%$[cite: 7] | $74.2\%$[cite: 7] | 14.2% reduced CPU stress[cite: 7] |
| **Max Temperature (30-min Soak Test)** | $62.4^\circ\text{C}$ (2 overruns)[cite: 7, 8] | **$58.1^\circ\text{C}$ (0 overruns)**[cite: 7, 8] | **Stable, no thermal throttling**[cite: 7, 8] |

### System Efficiency & Readability Metrics

* **Data Compression Ratio ($\rho$):** $\rho = \frac{1,521\text{ KB}}{4.088\text{ KB}} \approx 372\times$ reduction per frame[cite: 8].
* **24-Hour Bandwidth Usage:** Sending raw $1080\text{p}$ JPEG frames every 10 seconds requires $\sim 7.96\text{ GB/day}$[cite: 8]. Cortex text records reduce this to **$35.32\text{ MB/day}$**[cite: 8].
* **Retrieval Speed:**
  * $N = 1,000$ memories: $0.14\text{ ms}$[cite: 8]
  * $N = 10,000$ memories: $1.25\text{ ms}$ (costs $0.03\%$ of one BLIP step; no separate vector database needed)[cite: 7, 8].
* **Retrieval Accuracy ($N = 1,000$ memory pool, $50$ queries):**
  * **Acc@1:** $84.0\%$[cite: 8]
  * **Acc@3:** $96.0\%$[cite: 8]
  * **Mean Reciprocal Rank (MRR):** $0.89$[cite: 8]
* **Support Mode Wording & Readability:**
  * **Flesch Reading Ease Score:** Improves from $61.5$ (Standard) to **$84.2$** (Support Mode)[cite: 4, 8].
  * **Average Sentence Length:** Reduces from $16.2$ words to **$10.1$ words**[cite: 6, 8].
  * **Exact Clock Timestamps:** Reduced from $1.4$ per answer to **$0.0$** (replaced by relative terms like "earlier today")[cite: 6, 8].

---

## Care-Focused Support Mode

Cortex includes an accessibility configuration tailored for Alzheimer's patients based on grammatical complexity studies[cite: 6]:

+-----------------------------------------------------------------------------------+
| User Query: "Where is my laptop?"                                                 |
|                                                                                   |
| Standard Response:                                                                |
| "You left your laptop on the wooden desk at 2:15 PM today."                       |
|                                                                                   |
| Support Mode Response:                                                            |
| "Your laptop is on your desk."                                                    |
+-----------------------------------------------------------------------------------+

1. **Syntax Simplification:** Sentences are capped at $\sim 10$ words[cite: 6, 8].
2. **Relative Time Mapping:** Absolute timestamps ("2:15 PM") are converted into natural relative phrases ("earlier today")[cite: 6, 8].
3. **Calm Tone & Direct Fact Reporting:** Language never implies the user ought to have remembered[cite: 6].
4. **Speech Rate:** Synthesized voice output is slowed to $0.8\times$ speed for lower auditory processing strain[cite: 6].

---

## Software & Hardware Specifications

### Hardware Platform
* **Board:** Raspberry Pi 5 (8GB LPDDR4X RAM recommended)[cite: 6]
* **Camera:** Sony IMX708 Camera Module connected via CSI ribbon cable[cite: 6]
* **Power Supply:** USB-C PD (5V / 5A)[cite: 6]

### Software Stack
* **OS:** Raspberry Pi OS (Bookworm, 64-bit)[cite: 6]
* **Environment:** Python 3.11+[cite: 6]
* **Inference Libraries:** PyTorch (CPU Neon optimizations), Hugging Face Transformers, SentenceTransformers[cite: 6]
* **Backend Framework:** Flask, Flask-CORS
* **LLM Engine:** Ollama running `llama3.2:1b` (or Llama 3 RAG service)[cite: 4, 6]
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
