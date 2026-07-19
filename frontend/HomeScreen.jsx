// Add this near the top of App.jsx, after the CortexLogo component definition

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
        overflow: "hidden",
      }}
    >
      <AuroraBackground isDark={isDark} />

      <div style={{ position: "relative", zIndex: 1, width: "100%", maxWidth: 900, padding: "60px 24px" }}>
        {/* Theme toggle, top right */}
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

        {/* Hero */}
        <div style={{ textAlign: "center", marginBottom: 64 }}>
          <CortexLogo size={72} />
          <h1 style={{ fontSize: 44, fontWeight: 800, margin: "20px 0 10px", letterSpacing: -1 }}>Cortex</h1>
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

        {/* Feature grid */}
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
              <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 6 }}>{f.title}</div>
              <div style={{ fontSize: 13.5, color: colors.subtext, lineHeight: 1.5 }}>{f.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
