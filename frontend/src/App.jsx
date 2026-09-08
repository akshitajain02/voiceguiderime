import { useState } from "react";
import { readCurrentPage } from "./screenReader";
import { askAssistant } from "./api";
import { useEffect, useRef } from "react";
import logo from "./assets/logo.png.png";
import "./App.css";

function MicIcon() {
  return (
    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M12 15a3 3 0 0 0 3-3V6a3 3 0 0 0-6 0v6a3 3 0 0 0 3 3Z"
        stroke="#14100a"
        strokeWidth="1.8"
      />
      <path
        d="M19 11a7 7 0 0 1-14 0M12 18v3"
        stroke="#14100a"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
    </svg>
  );
}

function App() {
  const [query, setQuery] = useState("");
  const [reply, setReply] = useState("");
  const [loading, setLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [typedText, setTypedText] = useState("");
const fullHeadline = "Hear your screen, not just see it";

useEffect(() => {
  let i = 0;
  const interval = setInterval(() => {
    setTypedText(fullHeadline.slice(0, i + 1));
    i++;
    if (i === fullHeadline.length) clearInterval(interval);
  }, 45); // typing speed — 45ms per letter, adjust karke slow/fast kar sakte ho

  return () => clearInterval(interval);
}, []);
  const lastTapRef = useRef(0);

useEffect(() => {
  const handleTouchEnd = () => {
    const now = Date.now();
    if (now - lastTapRef.current < 350) {
      handleMicClick();
    }
    lastTapRef.current = now;
  };

  document.addEventListener("touchend", handleTouchEnd);
  return () => document.removeEventListener("touchend", handleTouchEnd);
}, []);

  const handleAsk = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setReply("");

    const screenData = readCurrentPage();
    const answer = await askAssistant(screenData, query);

    setReply(answer);
    setLoading(false);
  };

  // TODO (AssemblyAI integration point):
  // Jab AssemblyAI ka SDK/websocket ready ho, is function ke andar:
  // 1. isListening(true) karo, mic access lo (navigator.mediaDevices.getUserMedia)
  // 2. Audio stream ko AssemblyAI STT ko bhejo
  // 3. Jo text wapas mile, usse setQuery(text) karo
  // 4. Phir handleAsk() call karo automatically
  const handleMicClick = () => {
    setIsListening((prev) => !prev);
    // Abhi ke liye sirf visual toggle hai — asli STT wiring yahan aayegi
  };

  return (
    <div className="page">
      {/* ---------- HEADER ---------- */}
      <header className="header">
        <div className="logo">
  <img src={logo} alt="VoiceGuide logo" style={{ height: "28px" }} />
  VoiceGuide
</div>
        <nav className="header-nav">
          <span>How it works</span>
          <span>About</span>
        </nav>
      </header>

      {/* ---------- HERO / PROMOTIONS ---------- */}
      <section className="hero">
        <h1>{typedText}<span className="cursor">|</span></h1>
        <p>
          VoiceGuide listens, understands what's on your screen, and speaks back —
          without waiting for you to finish. Built for people who navigate the web
          by ear.
        </p>
        <div className="hero-badges">
          <span className="badge">Real-time interruption</span>
          <span className="badge">Powered by Rime voice</span>
          <span className="badge">Built for Smart India Hackathon</span>
        </div>
      </section>

      {/* ---------- HOW IT WORKS (real sequence, numbering justified) ---------- */}
      <section className="how-it-works">
        <h2>How it works</h2>
        <div className="steps">
          <div className="step">
            <div className="step-number">1</div>
            <h3>Speak your question</h3>
            <p>Tap the mic and ask anything about the page you're on, in your own words.</p>
          </div>
          <div className="step">
            <div className="step-number">2</div>
            <h3>It reads the screen</h3>
            <p>VoiceGuide scans what's visible right now — buttons, links, forms — silently.</p>
          </div>
          <div className="step">
            <div className="step-number">3</div>
            <h3>It replies out loud</h3>
            <p>You get a short spoken answer, and can interrupt anytime to ask something new.</p>
          </div>
        </div>
      </section>

      {/* ---------- ASSISTANT PANEL (core functional area) ---------- */}
      <section className="assistant-section">
        <div className="assistant-panel">
          <h2>Try VoiceGuide</h2>
          <p>Speak or type your question about this page below.</p>

          <button
            className={`mic-button ${isListening ? "listening" : ""}`}
            onClick={handleMicClick}
            aria-label={isListening ? "Stop listening" : "Start speaking"}
          >
            <MicIcon />
          </button>
          <div className="mic-status">
            {isListening ? "Listening..." : "Tap the mic to speak"}
          </div>

          <div className="input-row">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. login button kaha hai?"
              onKeyDown={(e) => e.key === "Enter" && handleAsk()}
              aria-label="Type your question"
            />
            <button className="ask-button" onClick={handleAsk} disabled={loading}>
              {loading ? "Thinking..." : "Ask"}
            </button>
          </div>

          {reply && (
            <div className="response-box">
              <p className="label">Response</p>
              <p>{reply}</p>
            </div>
          )}

          <div className="demo-form">
            <h3>Demo login form (for testing screen-reading)</h3>
            <label>
              Username
              <input type="text" placeholder="Enter username" />
            </label>
            <label>
              Password
              <input type="password" placeholder="Enter password" />
            </label>
            <button aria-label="Login Button">Login</button>
          </div>
        </div>
      </section>

      <footer className="footer">VoiceGuide — Smart India Hackathon</footer>
    </div>
  );
}

export default App;