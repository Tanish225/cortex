# CORTEX : Chat with your memories

### A Personal Memory Assistant for elderly people and alzheimer's care

CORTEX is a personal memory assistant designed to help people remember important moments from their day.

The idea is to capture useful moments, convert them into short text descriptions, and store those descriptions as searchable memories. Instead of keeping a large collection of personal images, CORTEX focuses on storing the information extracted from those images.

The user can then interact with CORTEX using natural language and ask questions about their previous experiences.

For example:

```text
What did I do this morning?

What was I working on yesterday?

Where did I see my laptop?

Remember that I have a meeting this evening.
```

CORTEX retrieves relevant memories and uses them as context to generate a response.

The current version is a software prototype. The next stage of the project is to explore moving the system toward an embedded and wearable platform using the **NXP FRDM-MCXN947 development board** available in our lab.

---

## What We Have Built

The current version of CORTEX implements the main software pipeline required for a personal memory assistant.

### 1. Visual Memory Capture

CORTEX can capture images from a camera at regular intervals.

The capture pipeline also performs basic filtering so that unnecessary or very similar frames are not continuously processed.

### 2. Image-to-Text Conversion

Useful frames are processed using **BLIP**, a vision-language model that converts an image into a short natural-language description.

For example:

```text
A person sitting at a desk working on a laptop.
```

The generated description becomes the memory representation used by the rest of the system.

The intention is to avoid making the original images the long-term memory of the system.

### 3. Text-Based Memory

The generated descriptions are stored as text memories along with their embeddings and relevant metadata.

This allows memories to be searched using their meaning rather than only matching exact words.

The system also maintains separate memories for different users.

### 4. Semantic Retrieval

When the user asks a question, the query is converted into an embedding.

CORTEX compares the query with the stored memory embeddings and retrieves the most relevant memories.

For example:

```text
What was I working on this afternoon?
```

can retrieve a memory such as:

```text
A person working on a laptop at a desk.
```

even though the words in the question and memory are not exactly the same.

### 5. Retrieval-Augmented Generation

The retrieved memories are passed to a local language model through **Ollama**.

The current implementation uses **Llama 3.2** to generate a response based on the retrieved memories.

The main pipeline is:

```text
Camera
   |
   v
Frame Capture
   |
   v
Frame Filtering
   |
   v
BLIP Image Captioning
   |
   v
Text Memory
   |
   v
Embedding Generation
   |
   v
Semantic Retrieval
   |
   v
Llama 3.2
   |
   v
Natural Language Response
```

---

# Current Features

The current prototype includes:

* Camera-based memory capture
* Automatic image captioning using BLIP
* Text-based memory representation
* Sentence-Transformer embeddings
* Semantic similarity search
* Retrieval-Augmented Generation
* Local Llama 3.2 integration using Ollama
* User authentication
* Separate memory storage for users
* Natural-language memory queries
* Voice input
* Text-to-speech responses
* Memory Support Mode
* Explicit remember commands
* Explicit forget commands
* Daily memory highlights
* Backend health/status checking
* React-based web interface

---

# Memory Support Mode

CORTEX includes a Memory Support Mode designed to make interaction simpler for users who may have difficulty recalling events or navigating a complex interface.

The mode focuses on:

* Simpler responses
* More direct answers
* Larger and clearer text
* A more conversational interaction style

The purpose is to explore how a memory assistant could make everyday recall easier.

CORTEX is a research and engineering prototype and is not intended to diagnose or treat any medical condition.

---

# Remember and Forget

CORTEX allows the user to explicitly control certain memories.

For example:

```text
Remember that I have a meeting at 6 PM.
```

The information can later be retrieved through a normal conversation.

The user can also request:

```text
Forget the meeting at 6 PM.
```

CORTEX searches for the relevant memory and removes it.

This is an important part of the project because the user should have control over what the system remembers.

---

# Privacy Approach

Privacy is one of the main ideas behind CORTEX.

The capture pipeline converts visual information into short text descriptions and uses those descriptions as the long-term memory representation.

The intended flow is:

```text
Camera Frame
     |
     v
Image Caption
     |
     v
Text Memory
     |
     v
Original Image Discarded
```

This reduces the need to maintain a permanent collection of personal photographs.

The current prototype also uses a locally running language model through Ollama instead of depending entirely on a hosted LLM API.

The privacy architecture will continue to be refined as the project moves toward the embedded and wearable stages.

---

# Technology Stack

| Component                 | Technology                |
| ------------------------- | ------------------------- |
| Frontend                  | React, Vite               |
| Backend                   | Python, Flask, Flask-CORS |
| Image Captioning          | BLIP                      |
| Embeddings                | Sentence-Transformers     |
| Retrieval                 | Cosine Similarity         |
| Language Model            | Llama 3.2                 |
| Local LLM Runtime         | Ollama                    |
| Voice Input               | Web Speech API            |
| Voice Output              | Web Speech API            |
| Current Platform          | Local Computer            |
| Planned Embedded Platform | NXP FRDM-MCXN947          |
| Planned Cloud Platform    | AWS                       |

---

# Project Structure

```text
cortex/
│
├── backend/
│   └── app.py
│
├── frontend/
│   └── src/
│       └── App.jsx
│
├── caption_photos.py
├── live_capture.py
├── query_memory.py
├── query_memory_rag.py
├── README.md
└── .gitignore
```

### `live_capture.py`

Handles the live camera pipeline, including frame capture, filtering, caption generation, and memory creation.

### `caption_photos.py`

Contains the image-captioning functionality used to convert captured images into text descriptions.

### `query_memory.py`

Contains an earlier implementation of the memory retrieval process.

### `query_memory_rag.py`

Contains the RAG-based memory retrieval and generation implementation.

### `backend/app.py`

Provides the Flask API used by the web application for authentication, memory retrieval, generation, highlights, and system status.

### `frontend/`

Contains the React web application and the user interface for interacting with CORTEX.

---

# Running CORTEX Locally

## Requirements

The current prototype requires:

* Python 3.11
* Node.js 18 or newer
* Git
* Ollama
* A working camera for live capture

Check the installed versions:

```bash
python3 --version
node --version
git --version
```

## 1. Clone the Repository

```bash
git clone https://github.com/Tanish225/cortex.git
cd cortex
```

## 2. Install Ollama

CORTEX uses Ollama to run the language model locally.

### Windows

Open PowerShell and run:

```powershell
irm https://ollama.com/install.ps1 | iex
```

Alternatively, download the Windows installer from the [official Ollama website](https://ollama.com/download/windows).

After installation, close and reopen PowerShell.

### macOS

Download and install Ollama from the [official Ollama website](https://ollama.com/download/mac).

### Linux

Run:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Verify the installation

```bash
ollama --version
```

If Ollama is not already running, start it with:

```bash
ollama serve
```

Keep this terminal open and use another terminal for the following commands.

### Download the model

CORTEX uses Llama 3.2:

```bash
ollama pull llama3.2
```

## 3. Create the Python Environment

### macOS / Linux

```bash
python3.11 -m venv venv
source venv/bin/activate
```

### Windows

```powershell
python -m venv venv
venv\Scripts\activate
```

Install the required Python packages:

```bash
pip install --upgrade pip
pip install torch transformers pillow sentence-transformers numpy opencv-python ollama flask flask-cors
```

## 4. Install Frontend Dependencies

Open another terminal:

```bash
cd cortex/frontend
npm install
```

## 5. Start the Camera Pipeline

From the project root:

```bash
python live_capture.py
```

This starts the camera capture and memory generation pipeline.

## 6. Start the Backend

Open another terminal:

```bash
cd cortex/backend
python app.py
```

The Flask backend runs locally on:

```text
http://localhost:5001
```

## 7. Start the Frontend

Open another terminal:

```bash
cd cortex/frontend
npm run dev
```

The React development server will normally be available at:

```text
http://localhost:5173
```

Open the frontend address in your browser.

---

# Example Interaction

After CORTEX has captured some memories, the user can ask questions such as:

```text
What did I do today?
```

```text
What was I working on this morning?
```

```text
Did I use my laptop today?
```

```text
What happened around lunchtime?
```

The system retrieves relevant memories and uses them as context for the response.

The user can also explicitly manage memories:

```text
Remember that I have a meeting this evening.
```

```text
Forget the meeting this evening.
```

---

# Embedded Hardware Direction

The current version of CORTEX runs primarily on a computer.

The next stage is to explore how the system can be moved toward a dedicated embedded and wearable platform.

Since the **NXP FRDM-MCXN947 development board** is available in our lab, we are currently considering it as the development platform for the embedded prototype.

The FRDM-MCXN947 is based on the MCXN947 microcontroller and provides a dual-core Arm Cortex-M33 platform with 2 MB flash and 1 MB RAM.

The board will allow us to explore the embedded side of CORTEX, including sensor interfaces, control logic, communication, preprocessing, and interaction with external AI services.

The goal is not necessarily to run the complete vision and language-model pipeline directly on the microcontroller.

Instead, we are exploring a hybrid architecture where computationally suitable tasks run on the embedded device while heavier AI workloads remain on a more capable edge or cloud system.

A possible architecture is:

```text
Camera / Sensors
       |
       v
FRDM-MCXN947
       |
       +----> Sensor Processing
       |
       +----> Event Detection
       |
       +----> Communication
       |
       v
Edge / Cloud AI
       |
       v
Memory + RAG
       |
       v
User Interaction
```

The exact division between embedded, edge, and cloud processing will be determined during development.

---

# Planned AWS Architecture

As the project develops, we are also considering a cloud-connected version of CORTEX.

A possible future architecture is:

```text
Wearable Device
       |
       v
AWS IoT Core
       |
       v
AWS Lambda
       |
       +------> DynamoDB
       |
       +------> AI / Bedrock
       |
       v
CORTEX Memory System
       |
       v
User
```

This is currently a planned architecture rather than an implemented deployment.

The purpose of exploring AWS is to understand how the local prototype could eventually support connected devices, scalable memory storage, and cloud-based AI services.

---

# Planned Location-Aware Memories

Another planned feature is location-aware memory.

A future version could associate memories with GPS information.

For example, instead of storing only:

```text
Had coffee.
```

CORTEX could store:

```text
Had coffee at [location].
```

This could enable questions such as:

```text
Where did I have coffee yesterday?
```

or:

```text
What did I do when I was at this location?
```

---

# Roadmap

## Completed

* [x] Camera-based memory capture
* [x] Frame filtering
* [x] BLIP image captioning
* [x] Text-based memory representation
* [x] Embedding generation
* [x] Semantic memory retrieval
* [x] RAG-based question answering
* [x] Local Llama 3.2 integration
* [x] React web interface
* [x] Flask backend
* [x] User authentication
* [x] User-specific memories
* [x] Voice interaction
* [x] Memory Support Mode
* [x] Remember and forget commands
* [x] Daily highlights

## In Progress

* [ ] Evaluate FRDM-MCXN947 for the embedded prototype
* [ ] Develop basic MCXN947 firmware
* [ ] Establish communication between the board and the CORTEX backend
* [ ] Test camera and sensor interfaces
* [ ] Determine which processing stages can run on the embedded platform
* [ ] Optimize the system for embedded resource constraints

## Planned

* [ ] Wireless connectivity
* [ ] AWS IoT Core integration
* [ ] AWS Lambda backend
* [ ] DynamoDB memory storage
* [ ] AWS Bedrock integration
* [ ] GPS-based memory tagging
* [ ] Wearable hardware prototype
* [ ] Low-power operation
* [ ] Compact wearable enclosure
* [ ] More efficient edge inference
* [ ] End-to-end wearable prototype

---

# Current Status

CORTEX currently has a working software prototype covering the main memory-assistant pipeline:

```text
Capture
  ↓
Caption
  ↓
Store
  ↓
Retrieve
  ↓
Generate
  ↓
Interact
```

The next phase is to move beyond the laptop-based prototype and investigate how this architecture can be implemented on dedicated embedded hardware.

The **FRDM-MCXN947** is currently being considered as the development platform for this stage.

The longer-term goal is to develop CORTEX into a privacy-focused wearable memory assistant that combines embedded hardware, edge/cloud computing, computer vision, semantic memory retrieval, and natural-language interaction.

---

# Disclaimer

CORTEX is an academic and engineering prototype.

It is not a medical device and should not be used for diagnosis, treatment, or medical decision-making.

---

## Author

**Tanish Sinha**

GitHub: https://github.com/Tanish225
