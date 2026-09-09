# VoiceGuide — Voice Assistant for Visually Impaired Users

Real-time voice AI that reads phone screens and guides navigation using natural conversation.

## Architecture

```
voice-agent/
├── agent.py                        # LiveKit Agent entrypoint (run this)
├── requirements.txt                # Python dependencies
├── stt/
│   └── deepgram_client.py          # STT factory (OpenAI Whisper / Deepgram swap)
├── llm/
│   └── prompt_builder.py           # screen_content + unheard → system prompt
├── interruption/
│   └── vad_handler.py              # interrupt() + cancel_pending_llm_call()
└── state/
    └── session_state.py            # "kaha tak bola / kya unheard hai" tracking
```

## Tech Stack

| Component | Provider |
|-----------|----------|
| Voice Activity Detection (VAD) | Silero |
| Speech-to-Text (STT) | OpenAI Whisper |
| LLM | Groq Qwen 3.8 27B |
| Text-to-Speech (TTS) | Rime (mist model) |
| Real-time transport | LiveKit |

## Setup

### 1. Install dependencies

```bash
cd voice-agent
pip install -r requirements.txt
```

### 2. Configure environment

Create `.env` in the repo root with:

```env
OPENAI_API_KEY=sk-...
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...
LIVEKIT_URL=wss://your-project.livekit.cloud
RIME_API_KEY=...
```

Get your Rime API key from [rime.ai](https://rime.ai).

### 3. Run the agent

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