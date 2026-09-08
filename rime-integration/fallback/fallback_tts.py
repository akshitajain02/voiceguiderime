"""Fallback TTS - ONLY used if Rime fails (network issue, auth error, etc).

Hackathon rule: "Make fallbacks visible... it must be disclosed."
So: log loudly whenever this path is used, and the README must state that
Rime is the default/primary provider in the judged flow.
"""

import logging

logger = logging.getLogger("fallback_tts")

# Simple local fallback using pyttsx3 (offline, no API key needed).
# pip install pyttsx3
try:
    import pyttsx3
    _engine = pyttsx3.init()
except ImportError:
    _engine = None


def speak_fallback(text: str, output_path: str = "fallback_output.wav") -> str:
    """Synthesize speech locally as a last resort. Returns the output file path."""
    logger.warning(f"[FALLBACK TTS ACTIVE] Rime was unavailable. Using offline fallback for: {text!r}")
    print("⚠️  FALLBACK TTS ACTIVE - Rime failed, using offline voice. This must be disclosed in demo/README.")

    if _engine is None:
        raise RuntimeError("pyttsx3 not installed. Run: pip install pyttsx3")

    _engine.save_to_file(text, output_path)
    _engine.runAndWait()
    return output_path


async def synthesize_with_fallback(rime_client, text: str, output_path: str = "output.mp3") -> tuple[str, str]:
    """Try Rime first; only fall back if it raises. Returns (path, provider_used)."""
    try:
        audio_bytes = await rime_client.synthesize_to_bytes(text)
        with open(output_path, "wb") as f:
            f.write(audio_bytes)
        return output_path, "rime"
    except Exception as exc:
        logger.error(f"Rime failed ({exc}), falling back to offline TTS.")
        fallback_path = speak_fallback(text)
        return fallback_path, "fallback"