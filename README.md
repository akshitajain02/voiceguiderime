# VoiceGuide : Rime Integrated Platform for Visually Impaired Users.

A real-time voice assistant that helps visually impaired users navigate web pages by speaking to them, built for **DataForge Rime Hackathon Challenge**.

VoiceGuide listens to a spoken question, reads the current webpage's content, and replies out loud through natural, interruptible speech — instead of forcing the user to wait for a full response before speaking again.

---

## Table of Contents
- [Architecture](#architecture)
- [Setup Instructions](#setup-instructions)
- [Third-Party Services](#third-party-services)
- [Rime Voice Integration Details](#rime-voice-integration-details)
- [Known Limitations](#known-limitations)
- [Failure Behavior](#failure-behavior)
- [Team & Module Ownership](#team--module-ownership)

---

## Architecture
User speaks
│
▼
[AssemblyAI STT] ──► transcribed text
│
▼
[Frontend: screenReader.js] ──► extracts visible page content (DOM)
│
▼
[Frontend: promptBuilder.js] ──► combines screen content + user query into an LLM prompt
│
▼
[LLM Backend] ──► decides the spoken response
│
▼
[Rime TTS] ──► converts response text to speech
│
▼
[LiveKit Agent] ──► streams audio back to user, handles interruption via VAD
│
▼
User hears response (can interrupt anytime)


**Core modules:**

| Module | Responsibility |
|---|---|
| Frontend (React) | UI, screen-content extraction, LLM prompt construction |
| Voice Pipeline / Backend | LiveKit agent, Deepgram/AssemblyAI STT, interrupt handling, state tracking |
| Rime Integration | Streaming TTS via WebSocket, voice selection, pronunciation handling |
| Integration & Testing | End-to-end wiring, automated interrupt-latency testing, status dashboard |

---

## Setup Instructions

### Prerequisites
- Node.js (v18+)
- npm
- API keys for: AssemblyAI, [LLM provider — FILL IN], Rime, LiveKit (see `.env.example`)

### Clone the repo
```bash
git clone https://github.com/prajjwalbaweja/VoiceGuide.git
cd VoiceGuide
```

### Frontend setup
```bash
cd frontend
npm install
npm run dev
```
App runs at `http://localhost:5173` (or next available port).

### Backend / Voice pipeline setup
```bash
cd voice-agent
[FILL IN — e.g. pip install -r requirements.txt / npm install]
[FILL IN — how to start the agent, e.g. python agent.py]
```

### Environment variables
Create a `.env` file in the relevant module folder with:


---

## Third-Party Services

| Service | Purpose |
|---|---|
| **AssemblyAI** | Speech-to-text (STT) — converts user's spoken question to text |
| **Rime** | Text-to-speech (TTS) — converts LLM's response to natural spoken audio |
| **LiveKit** | Real-time audio streaming + Voice Activity Detection (VAD) for interruption handling |
| **[LLM Provider — FILL IN]** | Decides the spoken response based on screen content + user query |

---

## Rime Voice Integration Details

| Field | Value |
|---|---|
| Model ID | `[FILL IN — e.g. mist-v2 / arcana]` |
| Speaker/Voice | `[FILL IN — e.g. "abbie", "marsh"]` |
| Language | `[FILL IN — e.g. en-US]` |
| Endpoint | `[FILL IN — e.g. wss://users.rime.ai/ws2]` |
| Audio Format | `[FILL IN — e.g. mp3 / pcm / mulaw, sample rate]` |
| Transport | `[FILL IN — e.g. WebSocket streaming]` |

*(To be filled in by the Rime Integration Lead — Akshita)*

---

## Known Limitations

- Screen-reading (`readCurrentPage()`) only detects elements currently visible in the viewport — content requiring scroll may be missed unless explicitly re-triggered.
- No persistent conversation memory — each question is treated independently.
- Pronunciation/number handling (e.g. reading "₹500" or "10:30 AM" naturally) is a stretch feature and may not be fully implemented depending on time constraints.
- Not tested across all browsers — primarily verified on Chrome.
- Backend LLM response time may add latency beyond what real-time voice interaction ideally requires.

---

## Failure Behavior

- **STT failure (AssemblyAI unreachable):** [FILL IN — e.g. falls back to text input, shows error message]
- **LLM/backend unreachable:** Frontend shows a fallback message: *"Sorry, main abhi jawab nahi de pa raha. Dobara try karo."* instead of crashing.
- **TTS failure (Rime unreachable):** [FILL IN — e.g. falls back to on-screen text response only]
- **No matching content on screen:** LLM is instructed to say so directly rather than guessing or inventing elements.
- **Network interruption mid-response:** [FILL IN — describe agent behavior]

---

## Team & Module Ownership

| Name | Role | Module |
|---|---|---|
| Prajjwal | Voice Pipeline / Backend Lead | `/voice-agent` |
| Akshita | Rime Integration Lead | `/rime-integration` |
| Abhayraj | Frontend + Screen-Understanding Lead | `/frontend` |
| Nihal | Integration, Test-Automation & Evidence Lead | `/testing-evidence` |

---

## License
