import streamlit as st
import json
import hashlib
from datetime import datetime
from sentence_transformers import SentenceTransformer, util
import ollama

LOG_FILE = "memory_log.json"
USERS_FILE = "users.json"
TOP_K = 5
MIN_SCORE = 0.15
SUMMARY_TRIGGERS = ["how was my day", "what did i do today", "summarize my day", "recap my day", "what happened today"]

st.set_page_config(page_title="Cortex", page_icon="🧠", layout="centered")

if "theme" not in st.session_state:
    st.session_state.theme = "dark"


def inject_css():
    if st.session_state.theme == "dark":
        bg = "linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 100%)"
        sidebar_bg = "#16161f"
        text_color = "#eaeaf0"
        caption_color = "#a0a0b0"
        bubble_bg = "#20202f"
    else:
        bg = "linear-gradient(180deg, #f7f7fb 0%, #eef0f8 100%)"
        sidebar_bg = "#ffffff"
        text_color = "#1a1a2e"
        caption_color = "#5c5c6e"
        bubble_bg = "#ffffff"

    st.markdown(f"""
    <style>
        .stApp {{
            background: {bg};
            color: {text_color};
        }}
        h1 {{
            font-family: 'Helvetica Neue', sans-serif;
            font-weight: 700;
            background: linear-gradient(90deg, #7f5af0, #2cb67d);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .stChatMessage {{
            border-radius: 16px;
            padding: 12px 16px;
            margin-bottom: 8px;
            background-color: {bubble_bg};
        }}
        section[data-testid="stSidebar"] {{
            background-color: {sidebar_bg};
        }}
        .stButton > button {{
            border-radius: 20px;
            border: 1px solid #7f5af0;
            color: #7f5af0;
            background: transparent;
            transition: all 0.2s ease;
        }}
        .stButton > button:hover {{
            background: #7f5af0;
            color: white;
        }}
        .stChatInput {{
            border-radius: 20px;
        }}
        .stCaption, p, span, label {{
            color: {caption_color} !important;
        }}
    </style>
    """, unsafe_allow_html=True)


inject_css()


# ---------- Auth helpers ----------

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


def check_login(username, password):
    users = load_users()
    if username not in users:
        return False
    return users[username] == hash_password(password)


def create_account(username, password):
    users = load_users()
    if username in users:
        return False
    users[username] = hash_password(password)
    save_users(users)
    return True


# ---------- Memory / RAG logic ----------

@st.cache_resource
def load_embed_model():
    return SentenceTransformer("all-MiniLM-L6-v2")


def load_memory_log():
    try:
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def humanize_timestamp(ts_string):
    dt = datetime.fromisoformat(ts_string)
    now = datetime.now()
    if dt.date() == now.date():
        day_part = "today"
    elif (now.date() - dt.date()).days == 1:
        day_part = "yesterday"
    else:
        day_part = dt.strftime("%B %d")
    time_part = dt.strftime("%I:%M %p").lstrip("0")
    return f"{day_part} at {time_part}"


def is_summary_question(query):
    q = query.lower().strip()
    return any(trigger in q for trigger in SUMMARY_TRIGGERS)


def get_todays_memories(memory_log):
    today = datetime.now().date()
    todays = [m for m in memory_log if datetime.fromisoformat(m["timestamp"]).date() == today]
    todays.sort(key=lambda m: m["timestamp"])
    return todays


def retrieve_memories(query, memory_log, embed_model, caption_embeddings):
    query_embedding = embed_model.encode(query, convert_to_tensor=True)
    scores = util.cos_sim(query_embedding, caption_embeddings)[0]
    top_results = scores.topk(min(TOP_K, len(memory_log)))

    retrieved = []
    for score, idx in zip(top_results.values, top_results.indices):
        idx = idx.item()
        retrieved.append({
            "caption": memory_log[idx]["caption"],
            "timestamp": memory_log[idx]["timestamp"],
            "score": score.item()
        })

    retrieved = [m for m in retrieved if m["score"] > MIN_SCORE]
    retrieved.sort(key=lambda m: m["timestamp"])
    return retrieved


def build_prompt(query, retrieved, is_summary=False):
    context_lines = [f"- {humanize_timestamp(m['timestamp'])}, saw: {m['caption']}" for m in retrieved]
    context = "\n".join(context_lines)

    pov_rules = """POV rules:
- If a memory describes hands, an object being held, or a close-up view, that is the user's OWN point of view — describe it as "you were holding/using..." (first person, direct).
- If a memory describes a full person, that is someone ELSE the camera saw — describe it as "you saw someone..." (third person, about another person).
- Never refer to the user themselves as "someone" or "the person" — the user is always "you"."""

    if is_summary:
        return f"""You are Cortex, a personal memory assistant speaking directly to the user.

The user asked a broad question about their whole day. Below is every memory captured today, in chronological order.

{pov_rules}

Rules:
- Go through the memories in order and mention the key distinct moments factually.
- Do NOT invent a narrative, feelings, transitions, or events not directly written in the memories.
- If two memories are basically the same thing, mention it once.
- Keep it a short list-like summary, not a story.

Today's memories:
{context}

Question: {query}

Answer:"""

    return f"""You are Cortex, a personal memory assistant speaking directly to the user.

The memories below are listed in the exact order they happened. These are judged most relevant to the question — they may not perfectly answer it.

{pov_rules}

Rules:
- Only state what is directly written in the memories below. Do not infer purpose, plans, or context not explicitly there.
- Do not invent objects, actions, locations, or events not word-for-word supported.
- If unsure these memories answer the question, say so, then list the key related memories with times instead of guessing.
- Keep the answer short and direct.

Memories:
{context}

Question: {query}

Answer:"""


def generate_answer(prompt):
    response = ollama.generate(model="llama3.2", prompt=prompt, options={"temperature": 0.1})
    return response["response"].strip()


def answer_question(query, memory_log, embed_model, caption_embeddings):
    if is_summary_question(query):
        todays = get_todays_memories(memory_log)
        if not todays:
            return "I don't have any memories from today."
        prompt = build_prompt(query, todays, is_summary=True)
    else:
        retrieved = retrieve_memories(query, memory_log, embed_model, caption_embeddings)
        if not retrieved:
            return "I don't have any memory related to that."
        prompt = build_prompt(query, retrieved, is_summary=False)

    return generate_answer(prompt)


# ---------- Streamlit UI ----------

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


def theme_toggle():
    label = "🌙 Dark" if st.session_state.theme == "dark" else "☀️ Light"
    if st.button(f"Switch theme ({label})"):
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
        st.rerun()


def login_page():
    theme_toggle()

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🧠 Cortex")
        st.caption("Your personal memory assistant — privacy-first, always on your side.")
        st.write("")

        tab1, tab2 = st.tabs(["Log In", "Create Account"])

        with tab1:
            username = st.text_input("Username", key="login_user", placeholder="Enter your username")
            password = st.text_input("Password", type="password", key="login_pass", placeholder="Enter your password")
            st.write("")
            if st.button("Log In", use_container_width=True):
                if check_login(username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("Incorrect username or password.")

        with tab2:
            new_username = st.text_input("Choose a username", key="signup_user", placeholder="Pick a username")
            new_password = st.text_input("Choose a password", type="password", key="signup_pass", placeholder="Pick a password")
            st.write("")
            if st.button("Create Account", use_container_width=True):
                if not new_username or not new_password:
                    st.error("Please fill in both fields.")
                elif create_account(new_username, new_password):
                    st.success("Account created! You can now log in.")
                else:
                    st.error("That username already exists.")


def chat_page():
    st.sidebar.title("🧠 Cortex")
    st.sidebar.write(f"Logged in as **{st.session_state.username}**")

    with st.sidebar:
        theme_toggle()

    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.rerun()

    embed_model = load_embed_model()
    memory_log = load_memory_log()
    st.sidebar.write(f"**{len(memory_log)}** memories loaded")

    st.title("🧠 Cortex")

    if not memory_log:
        st.info("No memories yet. Run live_capture.py first to start recording memories.")
        return

    captions = [entry["caption"] for entry in memory_log]
    caption_embeddings = embed_model.encode(captions, convert_to_tensor=True)

    for role, text in st.session_state.chat_history:
        avatar = "🧑" if role == "user" else "🧠"
        with st.chat_message(role, avatar=avatar):
            st.write(text)

    query = st.chat_input("Ask about your memories...")
    if query:
        st.session_state.chat_history.append(("user", query))
        with st.chat_message("user", avatar="🧑"):
            st.write(query)

        with st.chat_message("assistant", avatar="🧠"):
            with st.spinner("Thinking..."):
                answer = answer_question(query, memory_log, embed_model, caption_embeddings)
            st.write(answer)

        st.session_state.chat_history.append(("assistant", answer))


if st.session_state.logged_in:
    chat_page()
else:
    login_page()