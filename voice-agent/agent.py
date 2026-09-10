"""
agent.py — VoiceGuide LiveKit voice-agent entrypoint.

Uses livekit-agents v1.8.0 API:
  • Agent       – defines personality (instructions, LLM, STT, TTS, VAD)
  • AgentSession – manages the runtime session
"""

from __future__ import annotations

import json
import logging
import os
import sys

from dotenv import load_dotenv

# ── Load environment variables ──────────────────────────────────────
# .env lives one level up (repo root)
_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=_env_path)

# Add current directory to pythonpath so local modules resolve
sys.path.append(os.path.dirname(__file__))

from livekit import rtc
from livekit.agents import (
    Agent,
    AutoSubscribe,
    JobContext,
    JobProcess,
    cli,
    AgentServer,
)
from livekit.agents.voice import AgentSession
from livekit.plugins import groq, silero, rime

# ── Local modules ───────────────────────────────────────────────────
from stt.assemblyai_stt import create_stt
from llm.prompt_builder import PromptBuilder
from state.session_state import SessionState

# ── Logging ─────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-28s  %(levelname)-7s  %(message)s",
)
logger = logging.getLogger("voiceguide.agent")

# ====================================================================
# Pre-warm  (runs once per worker process)
# ====================================================================
def prewarm(proc: JobProcess) -> None:
    """
    Load heavy models once so that each room-join is fast.
    Silero VAD is ~2 MB and loads in <200 ms.
    """
    logger.info("Pre-warming: loading Silero VAD ...")
    proc.userdata["vad"] = silero.VAD.load()
    logger.info("Pre-warm complete.")

server = AgentServer(setup_fnc=prewarm)

# ====================================================================
# Entrypoint  (runs once per room / session)
# ====================================================================
@server.rtc_session()
async def entrypoint(ctx: JobContext) -> None:
    """Main agent entrypoint — one instance per LiveKit room."""

    # ── Per-session state objects ────────────────────────────────────
    session = SessionState()
    prompt_builder = PromptBuilder()

    # ── Build the system prompt ─────────────────────────────────────
    system_prompt = prompt_builder.build_system_prompt(session)

    # ── Create the Agent (personality / config) ─────────────────────
    agent = Agent(
        instructions=system_prompt,
        stt=create_stt(language="en"),
        llm=groq.LLM(
            model="qwen/qwen3.8-27b",
            api_key=os.environ.get("GROQ_API_KEY"),
            temperature=0.7,
        ),
        tts=rime.TTS(
            model="mist",
            speed_alpha=1.05,
        ),
        vad=ctx.proc.userdata["vad"],
        allow_interruptions=True,
        min_endpointing_delay=0.6,
    )

    # ── Create the AgentSession (runtime) ───────────────────────────
    agent_session = AgentSession()

    # ────────────────────────────────────────────────────────────────
    # DATA-CHANNEL: receive screen_content from companion Android app
    # ────────────────────────────────────────────────────────────────
    @ctx.room.on("data_received")
    def _on_data_received(packet: rtc.DataPacket) -> None:
        try:
            payload = json.loads(packet.data.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            logger.warning("Bad data-channel packet: %s", exc)
            return

        if "screen_content" in payload:
            session.update_screen_content(payload["screen_content"])
            logger.info(
                "Screen content updated (%d chars)",
                len(str(payload["screen_content"])),
            )
            # Refresh the agent's instructions with latest screen data
            new_prompt = prompt_builder.build_system_prompt(session)
            agent.update_instructions(new_prompt)
            session.clear_unheard()

    # ────────────────────────────────────────────────────────────────
    # PIPELINE EVENT HANDLERS
    # ────────────────────────────────────────────────────────────────

    @agent_session.on("user_input_transcribed")
    def _on_user_input(msg) -> None:
        """User finished speaking — transcript committed."""
        text = getattr(msg, "transcript", "") or ""
        logger.info("User: %s", text[:100])

        # ── Refresh instructions with latest screen content ──
        new_prompt = prompt_builder.build_system_prompt(session)
        agent.update_instructions(new_prompt)
        session.clear_unheard()

    @agent_session.on("agent_state_changed")
    def _on_agent_state_changed(state) -> None:
        logger.info("Agent state changed to: %s", state)

    # ────────────────────────────────────────────────────────────────
    # CONNECT & START
    # ────────────────────────────────────────────────────────────────
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    participant = await ctx.wait_for_participant()
    logger.info("Participant joined: %s", participant.identity)

    # Start the pipeline — v1.8.0 uses agent_session.start(agent)
    agent_session.start(agent, room=ctx.room)

    # ── Greeting ────────────────────────────────────────────────────
    await agent_session.say(
        "Hello! I'm VoiceGuide, your screen reading assistant. "
        "I can describe what's on your screen and help you navigate. "
        "Just ask me anything!",
        allow_interruptions=True,
    )
    logger.info("Agent started and greeting delivered.")


# ====================================================================
# CLI runner
# ====================================================================
if __name__ == "__main__":
    cli.run_app(server)