import { useState, useEffect, useRef } from "react";

const API_BASE = "http://localhost:5001/api";

// ---------- Helper: Synthesize a pleasant chime sound ----------
function playActivationChime() {
  try {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) return;
    const ctx = new AudioContext();

    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = "sine";
    osc.frequency.setValueAtTime(587.33, ctx.currentTime); // D5
    osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.15); // A5

    gain.gain.setValueAtTime(0.15, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.25);

    osc.connect(gain);
    gain.connect(ctx.destination);

    osc.start();
    osc.stop(ctx.currentTime + 0.25);
  } catch (e) {
    // AudioContext blocked or unsupported
  }
}

// ---------- Custom logo (no emoji, pure SVG) ----------
function CortexLogo({ size = 40 }) {
  const id = useRef(`grad-${Math.random().toString(36).slice(2)}`).current;
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" fill="none">
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="100" y2="100">
          <stop offset="0%" stopColor="#0a84ff" />
          <stop offset="100%" stopColor="#5e5ce6" />
        </linearGradient>
      </defs>
      <circle cx="50" cy="50" r="46" fill={`url(#${id})`} opacity="0.12" />
      <path
        d="M50 20 C34 20 24 32 24 46 C24 54 27 60 32 64 C30 68 30 73 33 77 C37 82 44 82 48 78"
        stroke={`url(#${id})`}
        strokeWidth="5"
        strokeLinecap="round"
        fill="none"
      />
      <path
        d="M50 20 C66 20 76 32 76 46 C76 54 73 60 68 64 C70 68 70 73 67 77 C63 82 56 82 52 78"
        stroke={`url(#${id})`}
        strokeWidth="5"
        strokeLinecap="round"
        fill="none"
      />
      <circle cx="50" cy="50" r="6" fill={`url(#${id})`} />
      <circle cx="36" cy="42" r="3" fill={`url(#${id})`} />
      <circle cx="64" cy="42" r="3" fill={`url(#${id})`} />
      <circle cx="41" cy="64" r="3" fill={`url(#${id})`} />
      <circle cx="59" cy="64" r="3" fill={`url(#${id})`} />
      <path d="M50 50 L36 42 M50 50 L64 42 M50 50 L41 64 M50 50 L59 64" stroke={`url(#${id})`} strokeWidth="2" opacity="0.6" />
    </svg>
  );
}

// ---------- Animated aurora background ----------
function AuroraBackground({ isDark }) {
  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        overflow: "hidden",
        zIndex: 0,
        background: isDark ? "#000000" : "#f5f5f7",
      }}
    >
      <style>{`
        @keyframes drift1 {
          0%, 100% { transform: translate(-10%, -10%) scale(1); }
          50% { transform: translate(10%, 15%) scale(1.2); }
        }
        @keyframes drift2 {
          0%, 100% { transform: translate(10%, 10%) scale(1.1); }
          50% { transform: translate(-15%, -5%) scale(0.9); }
        }
        @keyframes drift3 {
          0%, 100% { transform: translate(0%, 0%) scale(1); }
          50% { transform: translate(-10%, 15%) scale(1.15); }
        }
      `}</style>
      <div
        style={{
          position: "absolute",
          top: "-20%",
          left: "-10%",
          width: "60%",
          height: "60%",
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(10,132,255,0.35) 0%, transparent 70%)",
          filter: "blur(60px)",
          animation: "drift1 18s ease-in-out infinite",
        }}
      />
      <div
        style={{
          position: "absolute",
          top: "20%",
          right: "-15%",
          width: "55%",
          height: "55%",
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(94,92,230,0.3) 0%, transparent 70%)",
          filter: "blur(70px)",
          animation: "drift2 22s ease-in-out infinite",
        }}
      />
      <div
        style={{
          position: "absolute",
          bottom: "-20%",
          left: "20%",
          width: "50%",
          height: "50%",
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(48,209,88,0.18) 0%, transparent 70%)",
          filter: "blur(80px)",
          animation: "drift3 25s ease-in-out infinite",
        }}
      />
    </div>
  );
}

const FEATURES = [
  {
    icon: "◐",
    title: "Privacy-first memory",
    desc: "Only text descriptions are ever stored. Raw photos and video never leave your device.",
  },
  {
    icon: "✦",
    title: "Ask in plain English",
    desc: "\"Where's my laptop?\" \"What did I do today?\" — just ask, like talking to a friend.",
  },
  {
    icon: "🎙",
    title: "Speak or type",
    desc: "Full voice input and spoken replies, built in as an accessibility-first feature.",
  },
  {
    icon: "◑",
    title: "Daily highlights",
    desc: "A running recap of your day's key moments, always one tap away.",
  },
  {
    icon: "🧓",
    title: "Memory support mode",
    desc: "Simpler words, calmer answers, and larger text — designed for elderly and memory-impaired users.",
  },
  {
    icon: "⬡",
    title: "Yours alone",
    desc: "Every account's memories are private and fully separated from everyone else's.",
  },
];

function HomeScreen({ colors, isDark, setTheme, onGetStarted }) {
  return (
    <div
      style={{
        position: "relative",
        minHeight: "100vh",
        width: "100%",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        overflow: "auto",
      }}
    >
      <AuroraBackground isDark={isDark} />

      <div style={{ position: "relative", zIndex: 1, width: "100%", maxWidth: 900, padding: "60px 24px" }}>
        <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 20 }}>
          <button
            onClick={() => setTheme(isDark ? "light" : "dark")}
            style={{
              width: 36,
              height: 36,
              borderRadius: "50%",
              border: `1px solid ${colors.panelBorder}`,
              background: colors.panel,
              backdropFilter: "blur(10px)",
              cursor: "pointer",
              color: colors.text,
            }}
          >
            {isDark ? "☀" : "☾"}
          </button>
        </div>

        <div style={{ textAlign: "center", marginBottom: 64 }}>
          <CortexLogo size={72} />
          <h1 style={{ fontSize: 44, fontWeight: 800, margin: "20px 0 10px", letterSpacing: -1, color: colors.text }}>
            Cortex
          </h1>
          <p style={{ fontSize: 17, color: colors.subtext, maxWidth: 480, margin: "0 auto", lineHeight: 1.5 }}>
            A second memory you can talk to. Cortex quietly remembers your day, so you never have to.
          </p>

          <button
            onClick={onGetStarted}
            style={{
              marginTop: 32,
              padding: "14px 36px",
              borderRadius: 30,
              border: "none",
              background: "#0a84ff",
              color: "#fff",
              fontSize: 16,
              fontWeight: 600,
              cursor: "pointer",
              boxShadow: "0 8px 24px rgba(10,132,255,0.35)",
            }}
          >
            Getting Started
          </button>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
            gap: 16,
          }}
        >
          {FEATURES.map((f, i) => (
            <div
              key={i}
              style={{
                padding: "22px 20px",
                borderRadius: 20,
                background: colors.panel,
                border: `1px solid ${colors.panelBorder}`,
                backdropFilter: "blur(20px) saturate(160%)",
                WebkitBackdropFilter: "blur(20px) saturate(160%)",
              }}
            >
              <div style={{ fontSize: 22, marginBottom: 10, color: "#0a84ff" }}>{f.icon}</div>
              <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 6, color: colors.text }}>{f.title}</div>
              <div style={{ fontSize: 13.5, color: colors.subtext, lineHeight: 1.5 }}>{f.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ---------- Toast notifications ----------
function Toast({ toast, onDone }) {
  useEffect(() => {
    const t = setTimeout(onDone, 3000);
    return () => clearTimeout(t);
  }, [onDone]);

  const isError = toast.type === "error";
  return (
    <div
      style={{
        padding: "12px 18px",
        borderRadius: 14,
        background: isError ? "rgba(255,69,58,0.95)" : "rgba(48,209,88,0.95)",
        color: "#fff",
        fontSize: 14,
        fontWeight: 500,
        boxShadow: "0 8px 24px rgba(0,0,0,0.25)",
        backdropFilter: "blur(10px)",
        animation: "slideIn 0.25s ease",
        marginBottom: 8,
      }}
    >
      {toast.message}
    </div>
  );
}

function SettingRow({ label, value, onChange, colors }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 0" }}>
      <span style={{ fontSize: 14, color: colors.text }}>{label}</span>
      <button
        onClick={onChange}
        style={{
          width: 44,
          height: 26,
          borderRadius: 13,
          border: "none",
          background: value ? "#0a84ff" : colors.inputBg,
          position: "relative",
          cursor: "pointer",
          transition: "background 0.2s ease",
          flexShrink: 0,
          marginLeft: 12,
        }}
      >
        <span
          style={{
            position: "absolute",
            top: 3,
            left: value ? 21 : 3,
            width: 20,
            height: 20,
            borderRadius: "50%",
            background: "#fff",
            transition: "left 0.2s ease",
          }}
        />
      </button>
    </div>
  );
}

function IconButton({ onClick, children, colors, title }) {
  return (
    <button
      onClick={onClick}
      title={title}
      style={{
        width: 34,
        height: 34,
        borderRadius: "50%",
        border: "none",
        background: colors.inputBg,
        cursor: "pointer",
        fontSize: 15,
        color: colors.text,
      }}
    >
      {children}
    </button>
  );
}

function inputStyle(colors) {
  return {
    width: "100%",
    padding: "12px 14px",
    borderRadius: 12,
    border: "none",
    background: colors.inputBg,
    color: colors.text,
    fontSize: 14,
    outline: "none",
    boxSizing: "border-box",
  };
}

// ---------- Main App ----------
export default function App() {
  const [theme, setTheme] = useState("dark");
  const [view, setView] = useState("home"); // "home" | "auth" | "app"
  const [loggedIn, setLoggedIn] = useState(false);
  const [username, setUsername] = useState("");
  const [authMode, setAuthMode] = useState("login");
  const [authUsername, setAuthUsername] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [authError, setAuthError] = useState("");
  const [usernameStatus, setUsernameStatus] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [memoryCount, setMemoryCount] = useState(0);
  const [listening, setListening] = useState(false);
  const [speakEnabled, setSpeakEnabled] = useState(true);
  const [supportMode, setSupportMode] = useState(false); // memory support mode (elderly / Alzheimer's-friendly)
  const [showSettings, setShowSettings] = useState(false);
  const [showHighlights, setShowHighlights] = useState(false);
  const [highlights, setHighlights] = useState([]);
  const [todayDate, setTodayDate] = useState("");
  const [backendOnline, setBackendOnline] = useState(null);
  const [toasts, setToasts] = useState([]);

  const [wakeWordEnabled, setWakeWordEnabled] = useState(false);
  const [awaitingWakeWord, setAwaitingWakeWord] = useState(false);
  const [flashScreen, setFlashScreen] = useState(false);
  const autoSendRef = useRef(false);

  const wakeRecognitionRef = useRef(null);
  const chatEndRef = useRef(null);
  const recognitionRef = useRef(null);
  const usernameCheckTimeout = useRef(null);

  function pushToast(message, type = "success") {
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev, { id, message, type }]);
  }
  function removeToast(id) {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (loggedIn) {
      fetchMemoryCount();
      fetchHighlights();
    }
  }, [loggedIn]);

  useEffect(() => {
    async function checkHealth() {
      try {
        const res = await fetch(`${API_BASE}/health`);
        setBackendOnline(res.ok);
      } catch {
        setBackendOnline(false);
      }
    }
    checkHealth();
    const interval = setInterval(checkHealth, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recog = new SpeechRecognition();
      recog.continuous = false;
      recog.interimResults = false;
      recog.lang = "en-US";

      recog.onresult = (e) => {
        const transcriptText = e.results[0][0].transcript;
        setInput(transcriptText);
        setListening(false);

        // Hands-free trigger: if activated via wake word, automatically send query
        if (autoSendRef.current) {
          autoSendRef.current = false;
          sendMessage(transcriptText);
        }
      };

      recog.onerror = () => {
        setListening(false);
        autoSendRef.current = false;
      };

      recog.onend = () => {
        setListening(false);
      };

      recognitionRef.current = recog;
    }
  }, [username, supportMode]);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return;

    if (!wakeWordEnabled || !loggedIn || listening) {
      // stop background listening while a real question is being captured, or if disabled
      if (wakeRecognitionRef.current) {
        wakeRecognitionRef.current.stop();
        wakeRecognitionRef.current = null;
      }
      setAwaitingWakeWord(false);
      return;
    }

    const wakeRecog = new SpeechRecognition();
    wakeRecog.continuous = true;
    wakeRecog.interimResults = true;
    wakeRecog.lang = "en-US";

    wakeRecog.onresult = (e) => {
      const lastResult = e.results[e.results.length - 1];
      const transcript = lastResult[0].transcript.toLowerCase();

      if (transcript.includes("hey cortex") || transcript.includes("hey, cortex")) {
        wakeRecog.stop();

        // 1. Audio chime feedback
        playActivationChime();

        // 2. Visual screen flash feedback
        setFlashScreen(true);
        setTimeout(() => setFlashScreen(false), 400);

        // 3. Mark for automatic sending hands-free
        autoSendRef.current = true;

        setTimeout(() => toggleListening(), 300); // hand off to normal question capture
      }
    };

    wakeRecog.onerror = (e) => {
      if (e.error !== "no-speech" && e.error !== "aborted") {
        setAwaitingWakeWord(false);
      }
    };

    wakeRecog.onend = () => {
      // browsers auto-stop continuous recognition periodically — restart if still enabled
      if (wakeWordEnabled && loggedIn && !listening) {
        try {
          wakeRecog.start();
        } catch (e) {}
      }
    };

    wakeRecognitionRef.current = wakeRecog;
    setAwaitingWakeWord(true);
    try {
      wakeRecog.start();
    } catch (e) {}

    return () => {
      wakeRecog.stop();
    };
  }, [wakeWordEnabled, loggedIn, listening]);

  useEffect(() => {
    if (authMode !== "signup" || !authUsername.trim()) {
      setUsernameStatus(null);
      return;
    }
    clearTimeout(usernameCheckTimeout.current);
    usernameCheckTimeout.current = setTimeout(async () => {
      try {
        const res = await fetch(`${API_BASE}/check-username?username=${encodeURIComponent(authUsername.trim())}`);
        const data = await res.json();
        setUsernameStatus(data);
      } catch {
        setUsernameStatus(null);
      }
    }, 400);
    return () => clearTimeout(usernameCheckTimeout.current);
  }, [authUsername, authMode]);

  async function fetchMemoryCount() {
    try {
      const res = await fetch(`${API_BASE}/memory-count?username=${username}`);
      const data = await res.json();
      setMemoryCount(data.count || 0);
    } catch (e) {}
  }

  async function fetchHighlights() {
    try {
      const res = await fetch(`${API_BASE}/highlights?username=${username}`);
      const data = await res.json();
      setHighlights(data.highlights || []);
      setTodayDate(data.date || "");
    } catch (e) {}
  }

  async function handleAuth() {
    setAuthError("");
    if (!authUsername.trim() || !authPassword) {
      setAuthError("Please fill in both fields.");
      return;
    }
    const endpoint = authMode === "login" ? "login" : "signup";
    try {
      const res = await fetch(`${API_BASE}/${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: authUsername.trim(), password: authPassword }),
      });
      const data = await res.json();
      if (!res.ok) {
        setAuthError(data.error || "Something went wrong.");
        pushToast(data.error || "Something went wrong.", "error");
        return;
      }
      if (authMode === "signup") {
        setAuthMode("login");
        setAuthPassword("");
        pushToast("Account created! You can log in now.", "success");
        return;
      }
      setUsername(authUsername.trim());
      setLoggedIn(true);
      pushToast(`Welcome back, ${authUsername.trim()}!`, "success");
    } catch (e) {
      setAuthError("Could not reach the server. Is the backend running?");
      pushToast("Could not reach the server.", "error");
    }
  }

  function handleLogout() {
    setLoggedIn(false);
    setView("home");
    setUsername("");
    setMessages([]);
    setAuthUsername("");
    setAuthPassword("");
    pushToast("Logged out.", "success");
  }

  function speak(text) {
    if (!speakEnabled) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = supportMode ? 0.8 : 1.0;
    window.speechSynthesis.speak(utterance);
  }

  function toggleListening() {
    if (!recognitionRef.current) {
      pushToast("Speech recognition isn't supported in this browser. Try Chrome.", "error");
      return;
    }
    if (listening) {
      recognitionRef.current.stop();
      setListening(false);
    } else {
      recognitionRef.current.start();
      setListening(true);
    }
  }

  async function sendMessage(text) {
    const query = (text ?? input).trim();
    if (!query || loading) return;

    setMessages((prev) => [...prev, { role: "user", text: query }]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, query, support_mode: supportMode }),
      });
      const data = await res.json();
      const answer = data.answer || "Something went wrong.";
      setMessages((prev) => [...prev, { role: "assistant", text: answer }]);
      speak(answer);
    } catch (e) {
      setMessages((prev) => [...prev, { role: "assistant", text: "I couldn't reach the server." }]);
    } finally {
      setLoading(false);
    }
  }

  const isDark = theme === "dark";
  const colors = {
    bg: isDark ? "#000000" : "#f5f5f7",
    panel: isDark ? "rgba(28,28,30,0.6)" : "rgba(255,255,255,0.65)",
    panelBorder: isDark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.06)",
    text: isDark ? "#f5f5f7" : "#1d1d1f",
    subtext: isDark ? "rgba(235,235,245,0.6)" : "rgba(60,60,67,0.6)",
    userBubble: "#0a84ff",
    assistantBubble: isDark ? "rgba(58,58,60,0.9)" : "rgba(229,229,234,0.9)",
    assistantText: isDark ? "#f5f5f7" : "#1d1d1f",
    inputBg: isDark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.04)",
  };

  const bubbleFontSize = supportMode ? 19 : 15;
  const inputFontSize = supportMode ? 17 : 15;

  // ---------- Home screen (before auth) ----------
  if (!loggedIn && view === "home") {
    return <HomeScreen colors={colors} isDark={isDark} setTheme={setTheme} onGetStarted={() => setView("auth")} />;
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        width: "100%",
        background: isDark
          ? "radial-gradient(circle at 20% 20%, #1c1c2a 0%, #000000 60%)"
          : "radial-gradient(circle at 20% 20%, #ffffff 0%, #eef0f5 60%)",
        color: colors.text,
        fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, sans-serif",
        display: "flex",
        justifyContent: "center",
        alignItems: loggedIn ? "stretch" : "center",
        position: "relative",
      }}
    >
      <style>{`
        @keyframes slideIn { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
      `}</style>

      {/* Screen flash visual indicator */}
      {flashScreen && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(10, 132, 255, 0.25)",
            backdropFilter: "blur(4px)",
            zIndex: 9999,
            pointerEvents: "none",
            transition: "opacity 0.3s ease",
          }}
        />
      )}

      <div style={{ position: "fixed", top: 20, right: 20, zIndex: 1000, display: "flex", flexDirection: "column" }}>
        {toasts.map((t) => (
          <Toast key={t.id} toast={t} onDone={() => removeToast(t.id)} />
        ))}
      </div>

      <div
        style={{
          position: "fixed",
          top: 16,
          left: 16,
          zIndex: 1000,
          display: "flex",
          alignItems: "center",
          gap: 6,
          fontSize: 12,
          color: colors.subtext,
          background: colors.panel,
          padding: "6px 10px",
          borderRadius: 20,
          backdropFilter: "blur(10px)",
          border: `1px solid ${colors.panelBorder}`,
        }}
      >
        <span
          style={{
            width: 8,
            height: 8,
            borderRadius: "50%",
            background: backendOnline === null ? "#8e8e93" : backendOnline ? "#30d158" : "#ff453a",
            animation: backendOnline === null ? "pulse 1.5s infinite" : "none",
          }}
        />
        {backendOnline === null ? "Checking..." : backendOnline ? "Connected" : "Backend offline"}
      </div>

      {!loggedIn ? (
        // ---------- Auth screen ----------
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", padding: 20 }}>
          <div style={{ textAlign: "center", marginBottom: 24 }}>
            <CortexLogo size={56} />
            <h1 style={{ fontSize: 28, fontWeight: 800, margin: "12px 0 4px", letterSpacing: -0.5 }}>Cortex</h1>
            <p style={{ fontSize: 13, color: colors.subtext }}>Log in or create an account to continue</p>
          </div>

          <div
            style={{
              width: 380,
              padding: "32px 32px",
              borderRadius: 24,
              background: colors.panel,
              border: `1px solid ${colors.panelBorder}`,
              backdropFilter: "blur(30px) saturate(180%)",
              WebkitBackdropFilter: "blur(30px) saturate(180%)",
              boxShadow: isDark ? "0 8px 40px rgba(0,0,0,0.5)" : "0 8px 40px rgba(0,0,0,0.08)",
            }}
          >
            <div style={{ display: "flex", borderRadius: 12, background: colors.inputBg, padding: 4, marginBottom: 20 }}>
              {["login", "signup"].map((mode) => (
                <button
                  key={mode}
                  onClick={() => {
                    setAuthMode(mode);
                    setAuthError("");
                  }}
                  style={{
                    flex: 1,
                    padding: "8px 0",
                    borderRadius: 8,
                    border: "none",
                    fontSize: 14,
                    fontWeight: 600,
                    cursor: "pointer",
                    background: authMode === mode ? colors.userBubble : "transparent",
                    color: authMode === mode ? "#fff" : colors.text,
                    transition: "all 0.2s ease",
                  }}
                >
                  {mode === "login" ? "Log In" : "Sign Up"}
                </button>
              ))}
            </div>

            <input
              placeholder="Username"
              value={authUsername}
              onChange={(e) => setAuthUsername(e.target.value)}
              style={inputStyle(colors)}
            />

            {authMode === "signup" && usernameStatus && authUsername.trim() && (
              <div style={{ marginTop: 6, fontSize: 12.5 }}>
                {usernameStatus.available ? (
                  <span style={{ color: "#30d158" }}>✓ Available</span>
                ) : (
                  <div style={{ color: "#ff9f0a" }}>
                    <span>✗ Not available.</span>
                    {usernameStatus.suggestions?.length > 0 && (
                      <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 6 }}>
                        {usernameStatus.suggestions.map((s) => (
                          <button
                            key={s}
                            onClick={() => setAuthUsername(s)}
                            style={{
                              padding: "4px 10px",
                              borderRadius: 12,
                              border: `1px solid ${colors.panelBorder}`,
                              background: colors.inputBg,
                              color: colors.text,
                              fontSize: 12,
                              cursor: "pointer",
                            }}
                          >
                            {s}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            <input
              placeholder="Password"
              type="password"
              value={authPassword}
              onChange={(e) => setAuthPassword(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleAuth()}
              style={{ ...inputStyle(colors), marginTop: 10 }}
            />

            {authError && <p style={{ color: "#ff453a", fontSize: 13, marginTop: 10 }}>{authError}</p>}

            <button
              onClick={handleAuth}
              style={{
                width: "100%",
                marginTop: 18,
                padding: "12px 0",
                borderRadius: 12,
                border: "none",
                background: colors.userBubble,
                color: "#fff",
                fontSize: 15,
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              {authMode === "login" ? "Log In" : "Create Account"}
            </button>

            <button
              onClick={() => setView("home")}
              style={{
                width: "100%",
                marginTop: 14,
                padding: "10px 0",
                borderRadius: 12,
                border: `1px solid ${colors.panelBorder}`,
                background: "transparent",
                color: colors.subtext,
                fontSize: 13,
                cursor: "pointer",
              }}
            >
              ← Back to home
            </button>
          </div>
        </div>
      ) : (
        // ---------- Main chat app ----------
        <div style={{ width: "100%", maxWidth: 720, display: "flex", flexDirection: "column", height: "100vh" }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "16px 20px",
              borderBottom: `1px solid ${colors.panelBorder}`,
              background: colors.panel,
              backdropFilter: "blur(20px)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <CortexLogo size={30} />
              <div>
                <div style={{ fontWeight: 700, fontSize: 16 }}>Cortex</div>
                <div style={{ fontSize: 12, color: colors.subtext }}>{todayDate}</div>
              </div>
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              <IconButton onClick={() => setShowHighlights(!showHighlights)} colors={colors} title="Today's highlights">
                ✦
              </IconButton>
              <IconButton onClick={() => setShowSettings(!showSettings)} colors={colors} title="Settings">
                ⚙
              </IconButton>
              <IconButton onClick={handleLogout} colors={colors} title="Log out">
                ⎋
              </IconButton>
            </div>
          </div>

          {showHighlights && (
            <div
              style={{
                margin: "12px 20px 0",
                padding: 16,
                borderRadius: 16,
                background: colors.panel,
                border: `1px solid ${colors.panelBorder}`,
                backdropFilter: "blur(20px)",
              }}
            >
              <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 8, color: colors.subtext }}>
                TODAY'S HIGHLIGHTS
              </div>
              {highlights.length === 0 ? (
                <div style={{ fontSize: 13, color: colors.subtext }}>Nothing captured yet today.</div>
              ) : (
                highlights.map((h, i) => (
                  <div key={i} style={{ fontSize: 13.5, padding: "6px 0", borderTop: i > 0 ? `1px solid ${colors.panelBorder}` : "none" }}>
                    <span style={{ color: colors.subtext }}>{h.time} — </span>
                    {h.caption}
                  </div>
                ))
              )}
            </div>
          )}

          {showSettings && (
            <div
              style={{
                margin: "12px 20px 0",
                padding: 16,
                borderRadius: 16,
                background: colors.panel,
                border: `1px solid ${colors.panelBorder}`,
                backdropFilter: "blur(20px)",
              }}
            >
              <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 12, color: colors.subtext }}>
                ACCESSIBILITY
              </div>
              <SettingRow label="Speak responses aloud" value={speakEnabled} onChange={() => setSpeakEnabled(!speakEnabled)} colors={colors} />
              <SettingRow
                label='Wake word ("Hey Cortex")'
                value={wakeWordEnabled}
                onChange={() => setWakeWordEnabled(!wakeWordEnabled)}
                colors={colors}
              />
              <SettingRow label="Dark mode" value={isDark} onChange={() => setTheme(isDark ? "light" : "dark")} colors={colors} />
              <SettingRow
                label="Memory support mode (larger text, gentler answers)"
                value={supportMode}
                onChange={() => setSupportMode(!supportMode)}
                colors={colors}
              />
            </div>
          )}

          <div style={{ flex: 1, overflowY: "auto", padding: "20px 20px" }}>
            {messages.length === 0 && (
              <div style={{ textAlign: "center", color: colors.subtext, marginTop: 60, fontSize: 14 }}>
                Ask me anything about your day — try "what did I do today?"
              </div>
            )}
            {messages.map((m, i) => (
              <div key={i} style={{ display: "flex", justifyContent: m.role === "user" ? "flex-end" : "flex-start", marginBottom: 12 }}>
                <div
                  style={{
                    maxWidth: "75%",
                    padding: "10px 16px",
                    borderRadius: 18,
                    fontSize: bubbleFontSize,
                    lineHeight: 1.4,
                    background: m.role === "user" ? colors.userBubble : colors.assistantBubble,
                    color: m.role === "user" ? "#fff" : colors.assistantText,
                  }}
                >
                  {m.text}
                </div>
              </div>
            ))}
            {loading && (
              <div style={{ display: "flex", justifyContent: "flex-start", marginBottom: 12 }}>
                <div style={{ padding: "10px 16px", borderRadius: 18, background: colors.assistantBubble, color: colors.subtext, fontSize: 14 }}>
                  thinking...
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {awaitingWakeWord && !listening && (
            <div
              style={{
                textAlign: "center",
                fontSize: 12,
                color: colors.subtext,
                padding: "6px 0",
              }}
            >
              Listening for "Hey Cortex"...
            </div>
          )}

          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              padding: "14px 20px 22px",
              background: colors.panel,
              backdropFilter: "blur(20px)",
              borderTop: `1px solid ${colors.panelBorder}`,
            }}
          >
            <button
              onClick={toggleListening}
              style={{
                width: supportMode ? 48 : 40,
                height: supportMode ? 48 : 40,
                borderRadius: "50%",
                border: "none",
                flexShrink: 0,
                background: listening ? "#ff453a" : colors.inputBg,
                color: listening ? "#fff" : colors.text,
                fontSize: 16,
                cursor: "pointer",
              }}
              title="Speak your question"
            >
              🎤
            </button>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
              placeholder={listening ? "Listening..." : "Ask about your memories..."}
              style={{
                flex: 1,
                padding: supportMode ? "14px 18px" : "12px 16px",
                borderRadius: 20,
                border: "none",
                background: colors.inputBg,
                color: colors.text,
                fontSize: inputFontSize,
                outline: "none",
              }}
            />
            <button
              onClick={() => sendMessage()}
              disabled={loading || !input.trim()}
              style={{
                width: supportMode ? 48 : 40,
                height: supportMode ? 48 : 40,
                borderRadius: "50%",
                border: "none",
                background: colors.userBubble,
                color: "#fff",
                fontSize: 16,
                cursor: "pointer",
                opacity: loading || !input.trim() ? 0.5 : 1,
              }}
            >
              ↑
            </button>
          </div>
        </div>
      )}
    </div>
  );
}