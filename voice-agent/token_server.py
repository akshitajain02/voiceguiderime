"""
token_server.py — FastAPI token server for VoiceGuide LiveKit integration.

Generates signed JWT join tokens for frontend participants to connect to LiveKit rooms.
"""

from __future__ import annotations

import logging
import os
import sys
import uuid
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── Load environment variables ──────────────────────────────────────
_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=_env_path)

# Add current directory to sys.path
sys.path.append(os.path.dirname(__file__))

from livekit.api import AccessToken, VideoGrants

# ── Logging ─────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-28s  %(levelname)-7s  %(message)s",
)
logger = logging.getLogger("voiceguide.token_server")

# ── App initialization ──────────────────────────────────────────────
app = FastAPI(
    title="VoiceGuide Token Server",
    description="Issues LiveKit access tokens for VoiceGuide frontend clients",
    version="1.0.0",
)

# Enable CORS for React frontend (Vite runs on localhost:5173 by default)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LIVEKIT_API_KEY = os.environ.get("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.environ.get("LIVEKIT_API_SECRET")
LIVEKIT_URL = os.environ.get("LIVEKIT_URL")


class TokenResponse(BaseModel):
    """Token response schema returned to the frontend."""

    token: str
    url: str
    room: str
    identity: str


class TokenRequest(BaseModel):
    """Optional JSON payload for POST /token."""

    room: Optional[str] = "voiceguide-room"
    identity: Optional[str] = None


def generate_join_token(room_name: str, participant_identity: str) -> str:
    """
    Generate a signed LiveKit JWT access token with room join permissions.

    Args:
        room_name: The name of the room to join.
        participant_identity: Unique identity string for the participant.

    Returns:
        Signed JWT string.
    """
    if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
        logger.error("LIVEKIT_API_KEY or LIVEKIT_API_SECRET not found in environment!")
        raise HTTPException(
            status_code=500,
            detail="LiveKit credentials are not configured on the server.",
        )

    grant = VideoGrants(
        room_join=True,
        room=room_name,
        can_publish=True,
        can_subscribe=True,
        can_publish_data=True,
    )

    token = (
        AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        .with_identity(participant_identity)
        .with_name(participant_identity)
        .with_grants(grant)
        .to_jwt()
    )
    return token


@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint for the token server."""
    return {
        "status": "ok",
        "livekit_url": LIVEKIT_URL or "not_configured",
    }


@app.get("/token", response_model=TokenResponse)
def get_token(
    room: str = Query(default="voiceguide-room", description="LiveKit room name"),
    identity: Optional[str] = Query(default=None, description="Participant identity"),
) -> TokenResponse:
    """
    HTTP GET endpoint to fetch a LiveKit access token.

    Args:
        room: The room to join (default: "voiceguide-room").
        identity: Unique identity for the participant. If omitted, a random identity is generated.

    Returns:
        TokenResponse with signed token, LiveKit server URL, room name, and identity.
    """
    participant_id = identity if identity and identity.strip() else f"user-{uuid.uuid4().hex[:6]}"
    logger.info("Generating token for identity='%s' in room='%s'", participant_id, room)

    jwt_token = generate_join_token(room, participant_id)

    return TokenResponse(
        token=jwt_token,
        url=LIVEKIT_URL or "ws://localhost:7880",
        room=room,
        identity=participant_id,
    )


@app.post("/token", response_model=TokenResponse)
def post_token(request: TokenRequest) -> TokenResponse:
    """
    HTTP POST endpoint to fetch a LiveKit access token via JSON body.
    """
    room_name = request.room if request.room and request.room.strip() else "voiceguide-room"
    participant_id = (
        request.identity
        if request.identity and request.identity.strip()
        else f"user-{uuid.uuid4().hex[:6]}"
    )
    logger.info("Generating token for identity='%s' in room='%s' (POST)", participant_id, room_name)

    jwt_token = generate_join_token(room_name, participant_id)

    return TokenResponse(
        token=jwt_token,
        url=LIVEKIT_URL or "ws://localhost:7880",
        room=room_name,
        identity=participant_id,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("token_server:app", host="0.0.0.0", port=8000, reload=True)
