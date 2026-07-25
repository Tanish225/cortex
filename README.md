# Cortex

A second memory you can talk to.

Cortex is a privacy-first personal memory assistant. A camera captures moments throughout your day, an AI describes each one in a short caption, and you can later ask questions in plain English, by typing or speaking, to recall them. No raw photos or video are ever stored or transmitted, only text.

---

## What it does

- **Capture** — a camera grabs frames, skipping near-duplicate moments automatically
- **Caption** — BLIP (a vision-language AI model) describes each frame in a sentence
- **Store** — captions and their embeddings are saved once, per user, so retrieval stays fast even as your memory log grows
- **Retrieve** — questions are matched against stored memories using semantic search, not just keyword matching
- **Generate** — a local LLM (Llama 3.2) answers in natural, grounded sentences, with an optional gentler "memory support mode" for elderly or memory-impaired users
- **Remember and forget** — you can explicitly tell Cortex things ("remember that I have a meeting this evening") and later ask it to forget specific memories

This is a full RAG (Retrieval-Augmented Generation) pipeline behind a real web app, not just a script.

## Features

- Per-user accounts, with memories fully separated by user
- Clean chat interface with dark and light mode
- Speech-to-text input and text-to-speech replies
- Memory support mode — simpler words, calmer answers, and larger text, built for elderly and memory-impaired users
- Explicit "remember that..." and "forget..." commands
- Daily highlights, a quick recap of the day's key captured moments
- Live backend connection indicator
- Username availability checking with suggestions on signup

## Tech stack

| Layer | Tool |
|---|---|
| Captioning | BLIP (Hugging Face) |
| Retrieval | Sentence-Transformers, cosine similarity |
| Generation | Llama 3.2, via Ollama |
| Backend | Flask, Flask-CORS |
| Frontend | React (Vite) |
| Speech | Web Speech API |
| Planned hardware | PYNQ-Z2 or NXP i.MX 8M Plus |
| Planned cloud | AWS (IoT Core, Lambda, DynamoDB, Bedrock) |

---

## Setup

You'll need Python 3.11, Node.js 18 or newer, Ollama, and Git installed before starting. If you're not sure whether you have these, check with `python3 --version`, `node --version`, and `git --version` in a terminal first.

### Step 1: Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/cortex.git
cd cortex
```

### Step 2: Install Ollama and pull the model

Download Ollama from [ollama.com](https://ollama.com) for your operating system and install it like any normal app. Once it's installed and opened, run:

```bash
ollama pull llama3.2
```

This downloads the language model Cortex uses to generate answers, roughly 2GB, one-time download.

### Step 3: Set up Python and the backend

This step differs slightly between Mac and Windows, mainly in how you activate the virtual environment.

**On Mac:**

```bash
python3.11 -m venv venv
source venv/bin/activate
```

If `python3.11` isn't found, install it first with `brew install python@3.11`, then try again.

**On Windows (PowerShell):**

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

If PowerShell blocks the script from running, open PowerShell as Administrator and run `Set-ExecutionPolicy RemoteSigned`, then try activating again.

Once your virtual environment is active (you'll see `(venv)` at the start of your terminal line), install the dependencies:

```bash
cd backend
pip install --upgrade pip
pip install torch transformers pillow sentence-transformers numpy opencv-python ollama flask flask-cors
```

### Step 4: Set up the frontend

Open a new, separate terminal window for this (keep it apart from the backend terminal).

```bash
cd cortex/frontend
npm install
```

This installs all the React dependencies. It might take a minute or two the first time.

---

## Running Cortex

You'll need three terminals open at the same time, each doing a different job.

**Terminal 1: capture memories.** Run this while you want Cortex to actively record what it sees. You can skip this if you already have a `memory_log.json` file with data in it.

```bash
cd cortex
source venv/bin/activate        # Mac
venv\Scripts\Activate.ps1        # Windows
python live_capture.py
```

Press Ctrl+C when you want to stop capturing.

**Terminal 2: backend server.**

```bash
cd cortex/backend
source ../venv/bin/activate      # Mac
..\venv\Scripts\Activate.ps1     # Windows
python app.py
```

You should see it print that it's running on `http://localhost:5001`. Leave this terminal open the whole time you're using Cortex.

**Terminal 3: frontend.**

```bash
cd cortex/frontend
npm run dev
```

It'll print a local URL, usually `http://localhost:5173`. Open that in your browser.

---

## Using Cortex for the first time

1. Open the app in your browser. You'll land on the home screen.
2. Click Getting Started.
3. Create an account with a username and password.
4. Start asking Cortex about your day. Try "what did I do today?" as a first question.
5. Open the settings menu (the gear icon) to toggle voice input, spoken replies, dark or light mode, or memory support mode.

### A few things worth trying

```
remember that I have a meeting later this evening
```
Cortex will store this as a note you can ask about later.

```
forget the meeting
```
Cortex will find and remove the closest matching memory.

```
what did I do today?
```
Cortex reads through everything captured today and gives you a natural recap, rather than a raw list.

## Project structure

```
cortex/
  backend/
    app.py              backend API: auth, memory retrieval and generation, highlights, health check
    memory_log.json      stored memories, not tracked in git
    users.json           user accounts, not tracked in git
  frontend/
    src/
      App.jsx             the full React app: home screen, login, chat
  live_capture.py        captures frames from the camera, generates and caches captions and embeddings
  query_memory_rag.py    an earlier standalone command-line version, kept for reference
  README.md
```

## Troubleshooting

**"ollama: command not found"**
Make sure the Ollama app is actually installed and has been opened at least once. On Mac, check it's in your Applications folder.

**The app shows "backend offline"**
Check Terminal 2 is still running `python app.py` without errors. Also confirm nothing else on your machine is already using port 5001.

**Pip install fails or throws strange errors**
You're likely on the wrong Python version. Run `python --version` (or `python3 --version` on Mac) and confirm it says 3.11.x. If not, install Python 3.11 specifically and use that.

**Camera permission denied on Mac**
Go to System Settings, then Privacy and Security, then Camera, and enable access for Terminal or VS Code, whichever you're running the script from.

**Responses feel slow**
This should already be handled through embedding caching, but if you're still seeing slowness with a large memory log, confirm you're running the updated `live_capture.py`, since older captures without a cached embedding get backfilled automatically on first use, which briefly slows down just the very first query.

## Roadmap

- Full RAG pipeline with grounded, hallucination-resistant responses: done
- React frontend with auth, speech, accessibility, home screen: done
- Per-user memory isolation: done
- Cached embeddings for fast retrieval at scale: done
- Memory support mode for elderly and Alzheimer's-friendly use: done
- Explicit remember and forget commands: done
- Confirm and set up wearable board, either NXP i.MX 8M Plus or PYNQ-Z2: in progress
- Migrate backend to AWS, IoT Core through Lambda to DynamoDB and Bedrock: planned
- GPS-based location tagging: planned
- Wearable form factor packaging: planned

## Team

Built as a cloud computing course project.
