"""
assemblyai_stt.py — STT provider factory using AssemblyAI.

Uses AssemblyAI's real-time transcription via livekit-plugins-assemblyai.
Requires ASSEMBLYAI_API_KEY in your .env file.

Get your API key from: https://www.assemblyai.com/
"""

from __future__ import annotations

from livekit.plugins import assemblyai


def create_stt(
    *,
    language: str = "en",
):
    """
    Return a configured AssemblyAI STT instance.

    AssemblyAI provides real-time streaming transcription with
    high accuracy and built-in punctuation/formatting.
    """
    return assemblyai.STT(
        language=language,
    )
