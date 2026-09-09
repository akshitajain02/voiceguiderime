"""
session_state.py — "kaha tak bola / kya unheard hai" tracking.

Tracks:
  • Latest screen_content received from the companion app
  • Full conversation history (user + assistant messages)
  • Pending TTS text (what the agent *intends* to say)
  • Unheard segments (portions the user never heard due to interruption)
  • Interruption statistics
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class _UnheardSegment:
    """A chunk the agent tried to speak but was cut off."""
    text: str
    timestamp: float = field(default_factory=time.time)


class SessionState:
    """Per-room session state shared across all pipeline components."""

    def __init__(self) -> None:
        # ── Screen context (from LiveKit data-channel) ──────────────
        self._screen_content: dict[str, Any] | str | None = None
        self._screen_updated_at: float | None = None

        # ── Conversation history ────────────────────────────────────
        self._history: list[dict[str, str]] = []

        # ── Interrupt / unheard tracking ────────────────────────────
        self._pending_speech: str = ""          # text queued for TTS
        self._unheard: list[_UnheardSegment] = []
        self._interruption_count: int = 0

    # ────────────────────────────────────────────────────────────────
    # Screen content
    # ────────────────────────────────────────────────────────────────
    def update_screen_content(self, content: dict[str, Any] | str) -> None:
        """Called when new screen_content arrives via data-channel."""
        self._screen_content = content
        self._screen_updated_at = time.time()

    @property
    def screen_content(self) -> dict[str, Any] | str | None:
        return self._screen_content

    def get_screen_summary(self) -> str:
        """Return a human-readable summary of the current screen."""
        if self._screen_content is None:
            return (
                "No screen content available yet.  "
                "Ask the user to wait a moment while the screen loads."
            )

        content = self._screen_content

        # ── Plain string ────────────────────────────────────────────
        if isinstance(content, str):
            return content

        # ── Structured dict from companion app ──────────────────────
        if isinstance(content, dict):
            parts: list[str] = []

            if "app_name" in content:
                parts.append(f"Currently open app: {content['app_name']}")

            if "activity" in content:
                parts.append(f"Screen/Activity: {content['activity']}")

            if "elements" in content and isinstance(content["elements"], list):
                parts.append("— UI Elements —")
                for elem in content["elements"]:
                    etype = elem.get("type", "element")
                    text = elem.get("text", "")
                    desc = elem.get("content_description", "")
                    clickable = elem.get("clickable", False)
                    checked = elem.get("checked")
                    label = text or desc or "(no label)"
                    extras: list[str] = []
                    if clickable:
                        extras.append("tappable")
                    if checked is not None:
                        extras.append("checked" if checked else "unchecked")
                    suffix = f" ({', '.join(extras)})" if extras else ""
                    parts.append(f"  [{etype}] {label}{suffix}")

            if "raw_text" in content:
                parts.append(f"\nRaw screen text:\n{content['raw_text']}")

            if "notifications" in content:
                parts.append("— Notifications —")
                for notif in content["notifications"]:
                    parts.append(f"  • {notif}")

            return "\n".join(parts) if parts else str(content)

        return str(content)

    # ────────────────────────────────────────────────────────────────
    # Conversation history
    # ────────────────────────────────────────────────────────────────
    def add_user_message(self, text: str) -> None:
        self._history.append({"role": "user", "content": text})

    def add_assistant_message(self, text: str) -> None:
        self._history.append({"role": "assistant", "content": text})

    @property
    def conversation_history(self) -> list[dict[str, str]]:
        return list(self._history)

    # ────────────────────────────────────────────────────────────────
    # Pending speech / "kaha tak bola" tracking
    # ────────────────────────────────────────────────────────────────
    def set_pending_speech(self, text: str) -> None:
        """Store the full text the agent is *about* to speak."""
        self._pending_speech = text

    def mark_speech_interrupted(self, spoken_portion: str = "") -> None:
        """
        Called when the user interrupts.

        *spoken_portion*  – the part the TTS managed to output before
                           the interrupt fired (may be empty / partial).
        Anything remaining is saved as 'unheard'.
        """
        if not self._pending_speech:
            return

        unheard = self._pending_speech  # assume nothing was heard

        if spoken_portion:
            # Try to slice off the portion that WAS heard
            spoken_clean = spoken_portion.strip()
            idx = self._pending_speech.find(spoken_clean)
            if idx != -1:
                unheard = self._pending_speech[idx + len(spoken_clean):].strip()
            else:
                # Fallback: approximate by word count
                spoken_words = len(spoken_clean.split())
                full_words = self._pending_speech.split()
                if spoken_words < len(full_words):
                    unheard = " ".join(full_words[spoken_words:])

        if unheard:
            self._unheard.append(_UnheardSegment(text=unheard))

        self._interruption_count += 1
        self._pending_speech = ""

    def mark_speech_completed(self) -> None:
        """Called when the agent finishes speaking without interruption."""
        self._pending_speech = ""

    # ────────────────────────────────────────────────────────────────
    # "kya unheard hai" — retrieving & clearing unheard text
    # ────────────────────────────────────────────────────────────────
    def get_unheard_text(self) -> str | None:
        """
        Return a single string of everything the user didn't hear,
        or None if there's nothing pending.
        """
        if not self._unheard:
            return None
        # Only keep recent segments (discard anything > 5 min old)
        cutoff = time.time() - 300
        relevant = [s for s in self._unheard if s.timestamp >= cutoff]
        if not relevant:
            self._unheard.clear()
            return None
        return " … ".join(s.text for s in relevant)

    def clear_unheard(self) -> None:
        """Called after unheard text has been woven into a new response."""
        self._unheard.clear()

    @property
    def interruption_count(self) -> int:
        return self._interruption_count

    # ────────────────────────────────────────────────────────────────
    # Debug / repr
    # ────────────────────────────────────────────────────────────────
    def __repr__(self) -> str:
        return (
            f"<SessionState screen={'yes' if self._screen_content else 'no'} "
            f"history={len(self._history)} "
            f"unheard={len(self._unheard)} "
            f"interrupts={self._interruption_count}>"
        )
