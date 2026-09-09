"""
vad_handler.py — interrupt() + cancel_pending_llm_call().

Manages Voice Activity Detection (VAD) interrupt logic:
  • Detects when the user speaks while the agent is mid-response
  • Cancels any in-flight LLM request
  • Coordinates with SessionState to track unheard text
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from state.session_state import SessionState

logger = logging.getLogger("voiceguide.vad_handler")


class VADHandler:
    """
    Orchestrates interrupt behaviour for the VoiceGuide pipeline.

    Works alongside LiveKit's built-in VAD (Silero) — this class adds
    *application-level* interrupt semantics on top:
      1. Record that the agent was interrupted
      2. Save unheard text in SessionState
      3. Cancel any pending LLM generation
    """

    def __init__(self, session: SessionState) -> None:
        self._session = session
        self._pending_task: Optional[asyncio.Task] = None
        self._is_interrupted: bool = False
        self._interrupt_count: int = 0

    # ────────────────────────────────────────────────────────────────
    # Core interrupt lifecycle
    # ────────────────────────────────────────────────────────────────
    def interrupt(self, spoken_text: str = "") -> None:
        """
        Called when the user interrupts the agent mid-speech.

        Parameters
        ----------
        spoken_text : str
            The portion of the agent's response that was actually
            vocalised before the interrupt fired (may be partial).
        """
        self._is_interrupted = True
        self._interrupt_count += 1

        # Tell session to save whatever wasn't heard
        self._session.mark_speech_interrupted(spoken_text)
        logger.info(
            "Agent interrupted (total=%d). Spoken portion: '%s'",
            self._interrupt_count,
            spoken_text[:60] + ("…" if len(spoken_text) > 60 else ""),
        )

        # Kill any in-flight LLM generation
        self.cancel_pending_llm_call()

    # Alias so callers can use either name
    on_interrupt = interrupt

    def cancel_pending_llm_call(self) -> None:
        """Cancel the current LLM asyncio.Task, if one is running."""
        if self._pending_task is not None and not self._pending_task.done():
            self._pending_task.cancel()
            logger.debug("Pending LLM task cancelled.")
            self._pending_task = None

    # ────────────────────────────────────────────────────────────────
    # Task management
    # ────────────────────────────────────────────────────────────────
    def set_pending_task(self, task: asyncio.Task) -> None:
        """Register the current LLM task so it can be cancelled."""
        self._pending_task = task

    # ────────────────────────────────────────────────────────────────
    # Speech boundary hooks
    # ────────────────────────────────────────────────────────────────
    def on_speech_start(self) -> None:
        """Called when user begins speaking (VAD fires)."""
        self._is_interrupted = False

    def on_speech_end(self) -> None:
        """Called when user finishes speaking."""
        pass  # reserved for future use (e.g. analytics)

    def on_agent_speech_completed(self) -> None:
        """Called when the agent finishes speaking without interruption."""
        self._session.mark_speech_completed()
        self._is_interrupted = False

    # ────────────────────────────────────────────────────────────────
    # Properties
    # ────────────────────────────────────────────────────────────────
    @property
    def is_interrupted(self) -> bool:
        return self._is_interrupted

    @property
    def total_interrupts(self) -> int:
        return self._interrupt_count

    def reset(self) -> None:
        """Hard reset (e.g. on participant reconnect)."""
        self._is_interrupted = False
        self._pending_task = None
        self._interrupt_count = 0
