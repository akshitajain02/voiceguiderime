// src/App_example.jsx
// Reference Example: Using VoiceGuideConnection with LiveKit in React

import React, { useState, useEffect, useRef } from "react";
import { VoiceGuideConnection } from "./liveKitConnection";
import { readCurrentPage as extractScreenContent } from "./screenReader";

export function AppExample() {
  const [connectionState, setConnectionState] = useState("disconnected");
  const [speakingStatus, setSpeakingStatus] = useState({
    isLocalSpeaking: false,
    isAgentSpeaking: false,
  });
  const [errorMessage, setErrorMessage] = useState("");

  const connectionRef = useRef(null);

  useEffect(() => {
    // Initialize connection manager
    const connection = new VoiceGuideConnection({
      tokenServerUrl: "http://localhost:8000/token",
      onStateChange: (state) => {
        setConnectionState(state);
      },
      onSpeakingChange: (status) => {
        setSpeakingStatus(status);
      },
      onError: (err) => {
        setErrorMessage(err.message || "An error occurred");
      },
    });

    connectionRef.current = connection;

    return () => {
      // Disconnect on unmount
      connection.disconnect();
    };
  }, []);

  const handleStartVoiceGuide = async () => {
    setErrorMessage("");

    try {
      if (!connectionRef.current) return;

      // 1. Connect to LiveKit room and publish microphone
      await connectionRef.current.connect({
        room: "voiceguide-room",
      });

      // 2. Extract screen content using existing screenReader
      const screenData = extractScreenContent();

      // 3. Send screen context to backend agent via data channel
      await connectionRef.current.sendScreenContent(screenData);
    } catch (err) {
      console.error("Failed to start VoiceGuide:", err);
      setErrorMessage("Could not connect to VoiceGuide. Is token_server running?");
    }
  };

  const handleStopVoiceGuide = async () => {
    if (connectionRef.current) {
      await connectionRef.current.disconnect();
    }
  };

  return (
    <div style={{ padding: 24, fontFamily: "sans-serif" }}>
      <h2>VoiceGuide LiveKit Integration Example</h2>

      <div style={{ margin: "16px 0" }}>
        <p>
          <strong>Status:</strong> {connectionState}
        </p>
        {speakingStatus.isAgentSpeaking && (
          <p style={{ color: "#2563eb" }}>Agent is speaking...</p>
        )}
        {speakingStatus.isLocalSpeaking && (
          <p style={{ color: "#16a34a" }}>You are speaking...</p>
        )}
        {errorMessage && (
          <p style={{ color: "#dc2626" }}>{errorMessage}</p>
        )}
      </div>

      <div style={{ display: "flex", gap: 12 }}>
        {connectionState !== "connected" ? (
          <button
            onClick={handleStartVoiceGuide}
            disabled={connectionState === "connecting"}
            style={{
              padding: "10px 20px",
              background: "#000",
              color: "#fff",
              borderRadius: 8,
              cursor: "pointer",
            }}
          >
            {connectionState === "connecting" ? "Connecting..." : "Start VoiceGuide"}
          </button>
        ) : (
          <button
            onClick={handleStopVoiceGuide}
            style={{
              padding: "10px 20px",
              background: "#dc2626",
              color: "#fff",
              borderRadius: 8,
              cursor: "pointer",
            }}
          >
            Stop VoiceGuide
          </button>
        )}
      </div>
    </div>
  );
}

export default AppExample;
