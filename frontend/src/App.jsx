import { useState, useEffect, useRef } from "react";
import { readCurrentPage as extractScreenContent } from "./screenReader";
import { VoiceGuideConnection } from "./liveKitConnection";
import logo from "./assets/logo.png.png";
import "./App.css";

function MicIcon() {
  return (
    <svg
      width="32"
      height="32"
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
    >
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
  const [connectionState, setConnectionState] = useState("disconnected");
  const [speakingStatus, setSpeakingStatus] = useState({
    isLocalSpeaking: false,
    isAgentSpeaking: false,
  });
  const [query, setQuery] = useState("");
  const [reply, setReply] = useState("");
  const [loading, setLoading] = useState(false);
  const [typedText, setTypedText] = useState("");

  const fullHeadline = "Hear your screen, not just see it";

  // Refs
  const lastTapRef = useRef(0);
  const howItWorksRef = useRef(null);
  const assistantRef = useRef(null);
  const glassesRef = useRef(null);
  const connectionRef = useRef(null);

  // --------------------------------------------------
  // LIVEKIT CONNECTION INITIALIZATION
  // --------------------------------------------------

  useEffect(() => {
    const connection = new VoiceGuideConnection({
      tokenServerUrl: "http://localhost:8000/token",
      onStateChange: (state) => {
        setConnectionState(state);
        if (state === "connected") {
          setReply("Connected to VoiceGuide! Listening for your voice...");
        } else if (state === "disconnected") {
          setReply("");
        }
      },
      onSpeakingChange: (status) => {
        setSpeakingStatus(status);
        if (status.isAgentSpeaking) {
          setReply("VoiceGuide is speaking (Rime TTS)... Interrupt anytime by speaking!");
        } else if (status.isLocalSpeaking) {
          setReply("Listening to you...");
        }
      },
      onError: (err) => {
        console.error("VoiceGuide connection error:", err);
        setReply(`Connection error: ${err.message || "Failed to connect"}`);
      },
    });

    connectionRef.current = connection;

    return () => {
      connection.disconnect();
    };
  }, []);

  // --------------------------------------------------
  // HERO TYPING ANIMATION
  // --------------------------------------------------

  useEffect(() => {
    let i = 0;

    const interval = setInterval(() => {
      setTypedText(fullHeadline.slice(0, i + 1));
      i++;

      if (i === fullHeadline.length) {
        clearInterval(interval);
      }
    }, 45);

    return () => clearInterval(interval);
  }, []);

  // --------------------------------------------------
  // DOUBLE TAP FOR MICROPHONE
  // --------------------------------------------------

  useEffect(() => {
    const handleTouchEnd = () => {
      const now = Date.now();

      if (now - lastTapRef.current < 350) {
        handleMicClick();
      }

      lastTapRef.current = now;
    };

    document.addEventListener("touchend", handleTouchEnd);

    return () => {
      document.removeEventListener("touchend", handleTouchEnd);
    };
  }, []);

  // --------------------------------------------------
  // GLASSES SCROLL ANIMATION
  // --------------------------------------------------

  useEffect(() => {
    const handleScroll = () => {
      if (!assistantRef.current || !glassesRef.current) {
        return;
      }

      const assistantTop = assistantRef.current.offsetTop;
      const scrollY = window.scrollY;
      const viewportH = window.innerHeight;

      const denominator = assistantTop - viewportH * 0.4;

      let progress = 0;

      if (denominator <= 0) {
        progress = 1;
      } else {
        progress = Math.min(
          Math.max(scrollY / denominator, 0),
          1
        );
      }

      glassesRef.current.style.setProperty(
        "--scroll-progress",
        progress
      );
    };

    window.addEventListener("scroll", handleScroll, {
      passive: true,
    });

    handleScroll();

    return () => {
      window.removeEventListener("scroll", handleScroll);
    };
  }, []);

  // --------------------------------------------------
  // LIVEKIT START / STOP / MICROPHONE
  // --------------------------------------------------

  const handleMicClick = async () => {
    if (!connectionRef.current) return;

    if (connectionState === "connected") {
      await connectionRef.current.disconnect();
    } else if (connectionState !== "connecting") {
      try {
        setLoading(true);
        setReply("Connecting to VoiceGuide...");

        // 1. Connect to LiveKit room & publish microphone
        await connectionRef.current.connect({
          room: "voiceguide-room",
        });

        // 2. Extract screen content using existing screenReader
        const screenData = extractScreenContent();

        // 3. Send screen context to backend agent via data channel
        await connectionRef.current.sendScreenContent(screenData);
      } catch (err) {
        console.error("VoiceGuide start error:", err);
        setReply(
          "Could not connect to VoiceGuide. Please ensure token_server (port 8000) is running."
        );
      } finally {
        setLoading(false);
      }
    }
  };

  // --------------------------------------------------
  // ASK ASSISTANT / REFRESH SCREEN
  // --------------------------------------------------

  const handleAsk = async () => {
    if (loading) return;

    if (connectionState !== "connected") {
      await handleMicClick();
    } else if (connectionRef.current) {
      const screenData = extractScreenContent();
      await connectionRef.current.sendScreenContent(screenData);
      setReply(`Screen content updated and sent to VoiceGuide.`);
    }
  };

  // --------------------------------------------------
  // NAVIGATION
  // --------------------------------------------------

  const scrollToHowItWorks = () => {
    howItWorksRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  };

  const isListening = connectionState === "connected";


  return (
    <div className="page">

      {/* ==================================================
          HEADER
      ================================================== */}

      <header className="header">

        <div className="logo">
          <img
            src={logo}
            alt="VoiceGuide logo"
            style={{ height: "28px" }}
          />

          <span>VoiceGuide</span>
        </div>

        <nav
          className="header-nav"
          aria-label="Main navigation"
        >
          <button
            className="nav-link"
            onClick={scrollToHowItWorks}
          >
            How it works
          </button>

        
        </nav>

      </header>


      {/* ==================================================
          HERO / PROMOTIONS
      ================================================== */}

      <section className="hero">

        <h1>
          {typedText}
          <span className="cursor" aria-hidden="true">
            |
          </span>
        </h1>

        <p>
          VoiceGuide listens, understands what's on your
          screen, and speaks back without waiting for
          you to finish. Built for people who navigate the
          web by ear.
        </p>

        <div className="hero-badges">

          <span className="badge">
            Real-time interruption
          </span>

          <span className="badge">
            Powered by Rime voice
          </span>

          <span className="badge">
            Built for DataForge 2026
          </span>

        </div>

      </section>


      {/* ==================================================
          HOW IT WORKS
      ================================================== */}

      <section
        className="how-it-works"
        ref={howItWorksRef}
      >

        <h2>How it works</h2>

        <div className="steps">

          <div className="step">

            <div className="step-number">
              1
            </div>

            <h3>
              Speak your question
            </h3>

            <p>
              Tap the mic and ask anything about
              the page you're on, in your own words.
            </p>

          </div>


          <div className="step">

            <div className="step-number">
              2
            </div>

            <h3>
              It reads the screen
            </h3>

            <p>
              VoiceGuide scans what's visible right
              now buttons, links, forms silently.
            </p>

          </div>


          <div className="step">

            <div className="step-number">
              3
            </div>

            <h3>
              It replies out loud
            </h3>

            <p>
              You get a short spoken answer, and
              can interrupt anytime to ask something new.
            </p>

          </div>

        </div>

      </section>


      {/* ==================================================
          ASSISTANT SECTION
      ================================================== */}

      <section
        className="assistant-section"
        ref={assistantRef}
      >

        {/* Animated glasses background */}

        <div className="bg-orbs" aria-hidden="true">

          <span className="orb orb-1"></span>
          <span className="orb orb-2"></span>
          <span className="orb orb-3"></span>


          {/* Animated Chasma SVG */}

          <svg
            ref={glassesRef}
            className="chasma-bg"
            viewBox="0 0 400 200"
            aria-hidden="true"
          >

            <g>

              <circle
                className="lens lens-left"
                cx="130"
                cy="100"
                r="55"
              />

              <circle
                className="lens lens-right"
                cx="270"
                cy="100"
                r="55"
              />

              <line
                className="chasma-bridge"
                x1="185"
                y1="100"
                x2="215"
                y2="100"
              />

            </g>

          </svg>

        </div>


        {/* Actual assistant content */}

        <div className="assistant-panel">

          <h2>
            Try VoiceGuide
          </h2>

          <p>
            Speak or type your question about this page below.
          </p>


          {/* MICROPHONE */}

          <button
            className={`mic-button ${
              isListening ? "listening" : ""
            }`}
            onClick={handleMicClick}
            aria-label={
              connectionState === "connected"
                ? "Stop VoiceGuide"
                : connectionState === "connecting"
                ? "Connecting..."
                : "Start VoiceGuide"
            }
            aria-pressed={isListening}
          >

            <MicIcon />

          </button>


          <div
            className="mic-status"
            aria-live="polite"
          >
            {connectionState === "connecting"
              ? "Connecting to VoiceGuide..."
              : connectionState === "connected"
              ? speakingStatus.isAgentSpeaking
                ? "VoiceGuide is speaking (tap mic to stop)..."
                : speakingStatus.isLocalSpeaking
                ? "Listening to you..."
                : "VoiceGuide is active — ask anything or interrupt anytime"
              : "Tap the mic to start VoiceGuide"}
          </div>


          {/* TEXT INPUT */}

          <div className="input-row">

            <input
              type="text"
              value={query}
              onChange={(e) =>
                setQuery(e.target.value)
              }
              placeholder="e.g. login button kaha hai?"
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  handleAsk();
                }
              }}
              aria-label="Type your question"
            />

            <button
              className="ask-button"
              onClick={handleAsk}
              disabled={loading}
            >
              {loading
                ? "Connecting..."
                : connectionState === "connected"
                ? "Sync Screen"
                : "Start VoiceGuide"}
            </button>

          </div>


          {/* RESPONSE */}

          {reply && (

            <div
              className="response-box"
              aria-live="polite"
            >

              <p className="label">
                Response
              </p>

              <p>
                {reply}
              </p>

            </div>

          )}


          {/* DEMO LOGIN FORM */}

          <div className="demo-form">

            <h3>
              Demo login form
              <span> (for testing screen-reading)</span>
            </h3>


            <label>
              Username

              <input
                type="text"
                placeholder="Enter username"
              />
            </label>


            <label>
              Password

              <input
                type="password"
                placeholder="Enter password"
              />
            </label>


            <button aria-label="Login Button">
              Login
            </button>

          </div>

        </div>

      </section>


      {/* ==================================================
          FOOTER
      ================================================== */}

      <footer className="footer">
        VoiceGuide 
      </footer>

    </div>
  );
}

export default App;