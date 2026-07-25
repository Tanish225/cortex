# Cortex

A second memory you can talk to.

Cortex is a privacy-first personal memory assistant. A camera captures moments throughout your day, an AI describes each one in a short caption, and you can later ask questions in plain English -- by typing or speaking -- to recall them. No raw photos or video are ever stored or transmitted, only text.

---

## What it does

- **Capture** -- a camera grabs frames, skipping near-duplicate moments automatically
- **Caption** -- BLIP (a vision-language model) describes each frame in a sentence
- **Store** -- captions and their embeddings are saved once, per user
- **Retrieve** -- questions are matched against stored memories using semantic search
- **Generate** -- a local LLM (Llama 3.2) answers in natural, grounded sentences, with an optional gentler "memory support mode" for elderly or memory-impaired users
- **Remember / forget** -- you can explicitly tell Cortex to store a note ("remember that I have a meeting tonight") or remove one ("forget the meeting")

This is a full RAG (Retrieval-Augmented Generation) pipeline behind a real web app.

## Features

- Per-user accounts, memories fully separated by user
- Chat interface with dark and light mode
- Speech-to-text input, text-to-speech replies
- Memory support mode -- simpler words, calmer answers, larger text
- Daily highlights recap
- Live backend connection indicator
- Username availability checking with suggestions on signup
- Explicit remember / forget commands

## Tech stack

| Layer | Tool |
|---|---|
| Captioning | BLIP (Hugging Face) |
| Retrieval | Sentence-Transformers + cosine similarity |
| Generation | Llama 3.2 via Ollama |
| Backend | Flask + Flask-CORS |
| Frontend | React (Vite) |
| Speech | Web Speech API |
| Planned hardware | PYNQ-Z2 or NXP i.MX 8M Plus |
| Planned cloud | AWS (IoT Core, Lambda, DynamoDB, Bedrock) |

---

## Setup guide

You'll need Python 3.11, Node.js 18 or newer, Ollama, and Git installed before starting.

### Step 1 -- Clone the project

```bash
git clone https://github.com/YOUR_USERNAME/cortex.git
cd cortex
```

This works the same on Mac and Windows.

### Step 2 -- Install Ollama and pull the model

Download Ollama from [ollama.com](https://ollama.com) for your operating system and install it like any normal app. Once installed, open a terminal and run:

```bash
ollama pull llama3.2
```

This downloads the language model Cortex uses to generate answers, roughly 2GB, one-time only.

### Step 3 -- Set up Python and the backend

**On Mac:**

```bash
python3.11 -m venv venv
source venv/bin/activate
```

If `python3.11` isn't recognized, install it first with Homebrew:
```bash
brew install python@3.11
```

**On Windows (PowerShell):**

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

If PowerShell blocks the activation script, run this once first, then try again:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Confirm you're on the right Python version either way:
```bash
python --version
```
Should show 3.11.x. If it shows something else, you likely need to install Python 3.11 specifically and point the venv creation command at it.

Now install the required packages (same command for both operating systems, once your venv is active):

```bash
cd backend
pip install --upgrade pip
pip install torch transformers pillow sentence-transformers numpy opencv-python ollama flask flask-cors
cd ..
```

This step can take a few minutes, it's downloading a fair amount of machine learning libraries.

### Step 4 -- Set up the frontend

Open a separate terminal window for this, keep your backend terminal free for later.

```bash
cd cortex/frontend
npm install
```

---

## Running Cortex

You'll run three things at once, each in its own terminal window.

**Terminal 1 -- capture memories**

Only needed if you want to record new memories using your own camera. Skip this if you already have a `memory_log.json` to work from.

```bash
cd cortex
source venv/bin/activate        # Mac
venv\Scripts\Activate.ps1        # Windows

python live_capture.py
```

Let it run while you go about testing, press Ctrl+C to stop.

**Terminal 2 -- backend server**

```bash
cd cortex/backend
source ../venv/bin/activate      # Mac
..\venv\Scripts\Activate.ps1     # Windows

python app.py
```

You should see it print that it's running on `http://localhost:5001`. Leave this terminal open.

**Terminal 3 -- frontend**

```bash
cd cortex/frontend
npm run dev
```

It will print a local URL, usually `http://localhost:5173`. Open that in your browser.

---

## First-time use

1. Open the app in your browser -- you'll land on the home screen
2. Click Getting Started
3. Create an account with a username and password
4. Start asking Cortex about your captured memories, try "what did I do today?"
5. Open the settings menu (gear icon) to toggle voice input, spoken replies, dark or light mode, or memory support mode

## Talking to Cortex

A few things worth knowing:

- Ask naturally: "where's my laptop", "what did I do this morning", "how was my day"
- Tell it to remember something: "remember that I have a meeting this evening"
- Tell it to forget something: "forget the meeting"
- Casual messages like "thanks" or "hi" get quick, natural replies without going through memory search

## Project structure

```
cortex/
  backend/
    app.py              backend API -- auth, memory retrieval, question answering
    memory_log.json      stored memories, not committed to git
    users.json            user accounts, not committed to git
  frontend/
    src/App.jsx          the full interface
  live_capture.py        captures frames and generates captions
  query_memory_rag.py    an earlier command-line only version, kept for reference
  README.md
```

## Troubleshooting

| Problem | What to try |
|---|---|
| `ollama` command not found | Make sure the Ollama app is installed and has been opened at least once |
| App shows "backend offline" | Check Terminal 2 is actually running `python app.py` without errors |
| Pip install fails partway | Check `python --version` is 3.11.x, wrong Python version is the usual cause |
| Camera permission denied on Mac | System Settings, Privacy and Security, Camera, enable for Terminal or VS Code |
| PowerShell won't run activate script | Run the `Set-ExecutionPolicy` command shown in Step 3 above |
| Cortex gives a server error when you ask something | Check the backend terminal for a Python traceback and share it for debugging |

## Roadmap

- Full RAG pipeline with grounded, hallucination-resistant responses -- done
- React frontend with authentication, speech, accessibility settings -- done
- Per-user memory isolation -- done
- Cached embeddings for fast retrieval as memories grow -- done
- Remember and forget commands -- done
- Memory support mode for elderly and Alzheimer's-friendly use -- done
- Confirm and set up wearable board, either NXP i.MX 8M Plus or PYNQ-Z2 -- in progress
- Migrate backend to AWS, IoT Core through Lambda, DynamoDB, and Bedrock -- planned
- GPS-based location tagging -- planned
- Wearable form factor packaging -- planned

## Team

Built as a cloud computing course project.
