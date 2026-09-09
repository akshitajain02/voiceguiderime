import { useState, useEffect, useRef } from "react";
import { readCurrentPage } from "./screenReader";
import { askAssistant } from "./api";
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
  const [query, setQuery] = useState("");
  const [reply, setReply] = useState("");
  const [loading, setLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [typedText, setTypedText] = useState("");

  const fullHeadline = "Hear your screen, not just see it";

  // Refs
  const lastTapRef = useRef(0);
  const howItWorksRef = useRef(null);
  const assistantRef = useRef(null);
  const glassesRef = useRef(null);

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
  // ASK ASSISTANT
  // --------------------------------------------------

  const handleAsk = async () => {
    if (!query.trim() || loading) {
      return;
    }

    try {
      setLoading(true);
      setReply("");

      const screenData = readCurrentPage();

      const answer = await askAssistant(
        screenData,
        query
      );

      setReply(answer);
    } catch (error) {
      console.error("VoiceGuide error:", error);

      setReply(
        "Sorry, main abhi jawab nahi de pa raha. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  // --------------------------------------------------
  // MICROPHONE
  // --------------------------------------------------

  const handleMicClick = () => {
    setIsListening((prev) => !prev);
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
              isListening
                ? "Stop listening"
                : "Start speaking"
            }
            aria-pressed={isListening}
          >

            <MicIcon />

          </button>


          <div
            className="mic-status"
            aria-live="polite"
          >
            {isListening
              ? "Listening..."
              : "Tap the mic to speak"}
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
              disabled={loading || !query.trim()}
            >
              {loading
                ? "Thinking..."
                : "Ask"}
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