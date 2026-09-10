"""
prompt_builder.py — screen_content (shared schema) + query → LLM prompt.

Builds the system prompt for the VoiceGuide agent, injecting:
  • Latest screen accessibility data
  • Any unheard segments from interrupted responses
  • Conversational context hints
"""

from __future__ import annotations

from state.session_state import SessionState


class PromptBuilder:
    """Constructs system + user prompts for the VoiceGuide LLM pipeline."""

    # ── Base system prompt (always present) ─────────────────────────
    _SYSTEM_BASE = """\
You are **VoiceGuide**, an AI voice assistant designed to help visually \
impaired users understand and navigate their phone screen.

═══════════════════════════════════════════════════════════════
ROLE & CAPABILITIES
═══════════════════════════════════════════════════════════════
• You receive real-time accessibility data from the user's phone screen.
• Describe UI elements clearly: buttons, text fields, menus, lists, images.
• Guide navigation step-by-step — **one action at a time**.
• Help the user read messages, notifications, and on-screen text.

═══════════════════════════════════════════════════════════════
COMMUNICATION RULES
═══════════════════════════════════════════════════════════════
1. **Be concise.** The user is *listening*, not reading.  
   Aim for 2-3 sentences per response unless more detail is requested.
2. **Prioritise actionable info.** Lead with what matters most.
3. **Use natural language.** Say "there's a Send button" not  
   "ImageButton id=btn_send at coordinates (340,1200)".
4. **Avoid visual-spatial directions** like "top-right". Instead say  
   "after the search bar" or "the third item in the list".
5. **One step at a time.** When guiding a multi-step flow, give the  
   next step only after the user confirms the previous one.
6. **Never say** "I can see on the screen…" — say "On your screen  
   right now…" or "Currently showing…"
7. **Be honest.** If you're unsure about a UI element, say so.
8. **Confirm before acting.** Before saying "tap X", confirm the  
   user wants to proceed.
9. **Speak warmly.** Be patient, encouraging, and supportive.

═══════════════════════════════════════════════════════════════
SCREEN CONTENT SCHEMA
═══════════════════════════════════════════════════════════════
You will receive structured screen data that may include:
  • app_name — the currently open application
  • activity — the current screen or page name
  • elements[] — list of UI elements with type, text,  
    content_description, clickable, checked, focusable
  • raw_text — plain-text dump of visible text
  • notifications[] — pending notification banners
"""

    # ── Build full system prompt ────────────────────────────────────
    def build_system_prompt(self, session: SessionState) -> str:
        """
        Return the complete system prompt with live screen context
        and any unheard-text recovery instructions.
        """
        sections: list[str] = [self._SYSTEM_BASE]

        # ── Current screen ──────────────────────────────────────────
        screen = session.get_screen_summary()
        sections.append(
            "\n═══════════════════════════════════════════════════════════════\n"
            "CURRENT SCREEN CONTENT\n"
            "═══════════════════════════════════════════════════════════════\n"
            f"{screen}"
        )

        # ── Unheard / interrupted text recovery ────────────────────
        unheard = session.get_unheard_text()
        if unheard:
            sections.append(
                "\n═══════════════════════════════════════════════════════════════\n"
                "INTERRUPTED — UNHEARD INFORMATION\n"
                "═══════════════════════════════════════════════════════════════\n"
                f"Your previous response was interrupted. The user did NOT hear:\n"
                f'"{unheard}"\n\n'
                "If this information is still relevant to the user's new query, "
                "naturally weave it into your next response. Do NOT repeat it "
                "word-for-word — rephrase concisely. If it's no longer relevant, "
                "ignore it."
            )

        # ── Interruption frequency hint ─────────────────────────────
        if session.interruption_count >= 3:
            sections.append(
                "\n⚠️  The user has interrupted several times. Keep your "
                "responses even shorter — aim for 1 sentence where possible."
            )

        return "\n".join(sections)

    # ── Optionally augment the user query ───────────────────────────
    @staticmethod
    def build_user_prompt(user_query: str, session: SessionState) -> str:
        """
        Wrap the raw user transcript with any extra context.
        For now this is a pass-through; extend if needed.
        """
        return user_query
