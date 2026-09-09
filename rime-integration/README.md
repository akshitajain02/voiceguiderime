# Rime Integration — Akshita's Module

This folder is owned by **Akshita**.

## What to build
1. `rime_tts.py` — Rime streaming TTS class (WebSocket-based) compatible with LiveKit's TTS interface
2. Voice/model selection logic
3. "Writing for the ear" prompt tuning utilities
4. Pronunciation & number handling (Option B bonus — only if time permits)
5. Fallback TTS logic (if Rime is down, fall back to OpenAI TTS)

## Integration point
`agent.py` in `/voice-agent/` will import your TTS class:
```python
from rime_integration.rime_tts import RimeTTS
tts = RimeTTS(model="mist", speed=1.05)
```

## Key files to create
- `rime_tts.py` — Main TTS class
- `voice_config.py` — Voice/model selection
- `prompt_tuning.py` — "Writing for the ear" utilities
- `fallback.py` — Fallback TTS logic
