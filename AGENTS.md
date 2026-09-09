# VoiceGuide — Project Context for AI Agents

## What is this project?
VoiceGuide is a **real-time voice assistant for visually impaired users**.
It reads what's on a phone/web screen and describes it through natural voice conversation.
The user can interrupt the assistant mid-speech, and the agent gracefully handles it.

## Tech Stack
| Layer | Technology |
|-------|-----------|
| Real-time transport | LiveKit (Agents SDK, Python) |
| Speech-to-Text | AssemblyAI (real-time streaming) |
| LLM | Groq (qwen/qwen3.8-27b) |
| Text-to-Speech | Rime (mist model, WebSocket streaming) |
| VAD | Silero (via livekit-plugins-silero) |
| Frontend | HTML/CSS/JS web app |
| Testing | Python automated test harness |

## Folder Structure & Ownership
```
/voice-agent/          → Prajjwal  (LiveKit Agent, STT, VAD + interrupt, state)
/rime-integration/     → Akshita   (Rime streaming TTS, voice selection, prompt tuning)
/frontend/             → Abhayraj  (Web UI, DOM/accessibility extraction, LLM prompt design)
/testing-evidence/     → Nihal     (Automated test scripts, latency dashboard, RIME_EVIDENCE.md)
```

Each member works in their own folder → merge conflicts kam.

## Coding Conventions
- Python 3.11+, type hints everywhere
- `from __future__ import annotations` at top of every Python file
- Logging via `logging.getLogger("voiceguide.<module>")`
- Environment variables in root `.env` (never commit real keys)
- Docstrings on all public functions/classes

## Key Architecture Decisions
1. **Screen content** arrives via LiveKit data-channel as JSON (from companion app or web page extraction)
2. **Interrupt flow**: Silero VAD detects user speech → `VADHandler.interrupt()` fires → unheard text saved in `SessionState` → next LLM call gets unheard context injected via `PromptBuilder`
3. **Rime TTS** is a separate module (`/rime-integration`) that exposes a LiveKit-compatible TTS interface. `agent.py` imports it as a plugin.
4. **Testing**: Automated interrupt-latency test script runs 5 iterations, measures timestamps, outputs to `RIME_EVIDENCE.md`

## Integration Contract (How Modules Connect)

### Prajjwal → Akshita (TTS interface)
`agent.py` expects a TTS object compatible with `livekit.agents.tts.TTS` base class.
Akshita's `/rime-integration/rime_tts.py` should export a class that satisfies this interface.

### Abhayraj → Prajjwal (Screen content)
Frontend sends screen data to LiveKit room via data-channel:
```json
{
  "screen_content": {
    "app_name": "...",
    "elements": [{"type": "Button", "text": "Send", "clickable": true}],
    "raw_text": "..."
  }
}
```

### Nihal → Prajjwal (Test harness)
Test script connects to LiveKit room, triggers voice input, measures interrupt latency.

## Critical Success Criteria (for judges)
1. **Working interruption demo** — user interrupts mid-speech, agent stops and responds
2. **Honest failure case** — document what doesn't work
3. **Measured latency numbers** — 5 runs, interrupt latency in ms (RIME_EVIDENCE.md)
