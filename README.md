#  VoiceGuide

### Rime-Integrated Voice Assistant for Visually Impaired Users

> **VoiceGuide** is a real-time voice assistant designed to make web pages easier to navigate for visually impaired users. It understands what is currently visible on a webpage, listens to the user's question, and responds through natural, interruptible voice interaction.

Built for the **DataForge Rime Hackathon Challenge**.

<p align="center">
  <img src="https://img.shields.io/badge/React-18%2B-61DAFB?style=for-the-badge&logo=react&logoColor=white" />
  <img src="https://img.shields.io/badge/Rime-TTS-6C63FF?style=for-the-badge" />
  <img src="https://img.shields.io/badge/LiveKit-Realtime-FF6B35?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Accessibility-A11y-2E7D32?style=for-the-badge" />
</p>

---

##  What is VoiceGuide?

Navigating a modern webpage can be difficult without visual feedback. VoiceGuide addresses this by connecting **screen understanding, speech recognition, an LLM, and real-time voice synthesis** into a single interaction loop.

A user can simply ask something like:

 **"What options are available on this page?"**

VoiceGuide reads the relevant visible content, understands the question in context, and speaks the answer back.

The interaction is designed to feel conversational rather than like a traditional text-to-speech reader. Users can **interrupt the assistant while it is speaking** and continue the conversation naturally.

### The basic flow

**Speak → Understand the page → Generate an answer → Speak it back**

---

## Architecture

```text
┌──────────────────────┐
│        User          │
│   Speaks a question  │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│     AssemblyAI       │
│       STT            │
│ Speech → Text        │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│     screenReader.js  │
│                      │
│ Extract visible DOM  │
│ content from webpage │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│    promptBuilder.js  │
│                      │
│ Page content +       │
│ User query           │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│     LLM Backend      │
│                      │
│ Understand context   │
│ + generate response  │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│        Rime          │
│        TTS           │
│ Text → Speech        │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│       LiveKit        │
│                      │
│ Audio streaming +    │
│ VAD + interruption   │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│        User          │
│   Hears the answer   │
│   Can interrupt      │
└──────────────────────┘
```

### Core modules

| Module                       | Responsibility                                                               |
| ---------------------------- | ---------------------------------------------------------------------------- |
| **Frontend (React)**         | User interface, page-content extraction and prompt construction              |
| **Voice Pipeline / Backend** | LiveKit agent, STT integration, interruption handling and conversation state |
| **Rime Integration**         | Streaming text-to-speech, voice selection and pronunciation handling         |
| **Integration & Testing**    | End-to-end integration, interrupt-latency testing and evidence collection    |



##  Getting Started

### Prerequisites

Make sure the following are installed before running the project:

* **Node.js 18+**
* **npm**
* API credentials for:

  * AssemblyAI
  * Rime
  * LiveKit
  * LLM provider

Environment variable names and configuration details are documented in `.env.example`.

---

### 1. Clone the repository

```bash
git clone https://github.com/prajjwalbaweja/VoiceGuide.git
cd VoiceGuide
```

---

### 2. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

The development server will normally be available at:

```text
http://localhost:5173
```

If that port is already in use, Vite will automatically select another available port.

---

### 3. Start the voice agent

```bash
cd voice-agent

# Development mode (auto-reload, connects to LiveKit Cloud)
python agent.py dev

# Production mode
python agent.py start
```

## How It Works

### Data Flow

```
Phone App  ──data-channel──►  LiveKit Room  ──►  VoiceGuide Agent
  (screen_content JSON)                            │
                                                   ├─ STT: Whisper transcribes user speech
                                                   ├─ LLM: GPT-4o-mini reasons about screen
                                                   ├─ TTS: Rime speaks the response
                                                   └─ VAD: Silero detects interrupts
```

### Screen Content Protocol

The companion app sends screen accessibility data via LiveKit data-channel as JSON:

```json
{
  "screen_content": {
    "app_name": "WhatsApp",
    "activity": "ChatActivity",
    "elements": [
      {
        "type": "TextView",
        "text": "Hey, are you free today?",
        "content_description": "",
        "clickable": false
      },
      {
        "type": "Button",
        "text": "Send",
        "content_description": "Send message",
        "clickable": true
      }
    ],
    "notifications": ["2 new messages from Mom"]
  }
}
```

### Interrupt Logic ("kaha tak bola / kya unheard hai")

1. Agent starts speaking a response via TTS
2. User interrupts mid-speech (detected by Silero VAD)
3. `VADHandler.interrupt()` fires:
   - Saves the **unheard portion** of the response in `SessionState`
   - Cancels any pending LLM generation
4. On the next LLM call, `PromptBuilder` injects the unheard text into the system prompt
5. The LLM naturally weaves any still-relevant unheard info into its next response

## Team

| Member | Role |
|--------|------|
| **Prajjwal** | Voice Pipeline / Backend Lead — LiveKit Agent, STT, VAD + interrupt logic, state tracking |

# Install dependencies
[FILL IN — e.g. pip install -r requirements.txt]

# Start the agent
[FILL IN — e.g. python agent.py]
```
 **Note:** The exact backend commands depend on the final voice-agent implementation.

---

## Third-Party Services

VoiceGuide combines multiple services, with each one handling a specific part of the voice interaction pipeline.

| Service          | Used For                                                                         |
| ---------------- | -------------------------------------------------------------------------------- |
| **AssemblyAI**   | Speech-to-text — converts the user's spoken question into text                   |
| **Rime**         | Text-to-speech — generates natural spoken responses                              |
| **LiveKit**      | Real-time audio transport, streaming and interruption/VAD handling               |
| **LLM Provider** | Understands the user's query and visible page content and generates the response |

---

##  Rime Voice Integration

Rime is used as the final speech layer of VoiceGuide.

Instead of waiting for an entire response before generating audio, the integration is designed around **streaming speech**, helping reduce perceived response latency and making interruptions possible.

### Current Rime configuration

| Configuration       | Value                             |
| ------------------- | --------------------------------- |
| **Model ID**        | `mistv3`                       |
| **Speaker / Voice** | `[FILL IN]`                       |
| **Language**        | `[FILL IN]`                       |
| **Endpoint**        | `[FILL IN]`                       |
| **Audio Format**    | `[FILL IN]`                       |
| **Transport**       | `[FILL IN — WebSocket streaming]` |

Rime-specific configuration will be finalized by the **Rime Integration Lead**.

---

##  Accessibility Focus

VoiceGuide is built around a simple idea:

**Users should be able to interact with web content without depending entirely on visual navigation.**

The project focuses on:

*  **Voice-first interaction**
*  **Understanding visible webpage content**
*  **Natural spoken responses**
*  **Low-latency interaction**
*  **Interruptible speech**
*  **Context-aware answers**
*  **Avoiding fabricated information when content is unavailable**

The assistant is instructed to answer based on the content available on the page rather than guessing about elements it cannot identify.

---

##  Interruptible Voice Interaction

One of the key parts of VoiceGuide is that the assistant does **not** require the user to wait until the response finishes.

For example:

```text
Assistant: "There are three options available on this page..."
User:      "Stop. What is the second one?"
Assistant: "The second option is..."
```

LiveKit's real-time audio pipeline and VAD help detect the user's interruption and allow the current response to be stopped.

This makes the interaction closer to a normal voice conversation.

---

##  Failure Behavior

VoiceGuide is designed to fail gracefully when one of the external services becomes unavailable.

| Situation                    | Expected behavior                                                          |
| ---------------------------- | -------------------------------------------------------------------------- |
| **STT unavailable**          | `[FILL IN — fallback behavior]`                                            |
| **LLM/backend unavailable**  | Display/speak a fallback response instead of crashing                      |
| **Rime unavailable**         | `[FILL IN — fallback behavior]`                                            |
| **No relevant page content** | Assistant explicitly says that it could not find the requested information |
| **Network interruption**     | `[FILL IN — agent behavior]`                                               |

Example fallback response:

> *"Sorry, main abhi jawab nahi de pa raha. Dobara try karo."*

The system should prefer being transparent about missing information rather than inventing an answer.

---

##  Known Limitations

The current implementation has a few known limitations:

* `readCurrentPage()` primarily captures content that is currently visible in the viewport. Content requiring scrolling may not be available until the process is triggered again.
* There is currently **no persistent conversation memory**; questions are treated independently.
* Pronunciation and number normalization — for example, naturally speaking values such as `₹500` or `10:30 AM` — may require further refinement.
* Testing has primarily focused on **Chrome** rather than all major browsers.
* LLM response generation can introduce additional latency into the voice pipeline.
* Final Rime configuration and some failure fallbacks are still subject to integration testing.

---

##  Testing & Evidence

The project includes testing around the complete interaction pipeline:

```text
User Input
    ↓
Speech Recognition
    ↓
Page Understanding
    ↓
LLM Response
    ↓
Rime TTS
    ↓
Audio Streaming
    ↓
User Interruption
```

Important areas to validate include:

* End-to-end response latency
* Speech recognition accuracy
* Page-content extraction
* Response relevance
* Rime audio generation
* Audio streaming reliability
* Interruption detection
* Recovery from service/network failures

---

##  Team & Module Ownership

| Team Member  | Role                                         | Primary Module      |
| ------------ | -------------------------------------------- | ------------------- |
| **Prajjwal** | Voice Pipeline / Backend Lead                | `/voice-agent`      |
| **Akshita**  | Rime Integration Lead                        | `/rime-integration` |
| **Abhayraj** | Frontend + Screen Understanding Lead         | `/frontend`         |
| **Nihal**    | Integration, Test Automation & Evidence Lead | `/testing-evidence` |

Each module is developed independently and integrated through the shared voice interaction pipeline.

---

##  Project Structure

```text
VoiceGuide/
│
├── frontend/
│   ├── src/
│   │   ├── screenReader.js
│   │   ├── promptBuilder.js
│   │   └── ...
│   └── ...
│
├── voice-agent/
│   └── ...
│
├── rime-integration/
│   └── ...
│
├── testing-evidence/
│   └── ...
│
├── .env.example
└── README.md
```

The structure may evolve as the different modules are integrated.

---

##  Project Goal

VoiceGuide aims to demonstrate how **real-time voice AI can make everyday web interaction more accessible**.

The goal isn't simply to read a webpage aloud. It is to let users **ask questions about what they are currently viewing and interact with the answer conversationally**.

---

## 📜 License

This project was developed as part of the **DataForge Rime Hackathon Challenge 2026**.
