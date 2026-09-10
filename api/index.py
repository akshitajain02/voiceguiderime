"""
api/index.py — Vercel Serverless Function entrypoint for VoiceGuide LiveKit Token API.
"""

from __future__ import annotations

import os
import uuid
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from livekit.api import AccessToken, VideoGrants

app = FastAPI(title="VoiceGuide Token API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LIVEKIT_API_KEY = os.environ.get("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.environ.get("LIVEKIT_API_SECRET")
LIVEKIT_URL = os.environ.get("LIVEKIT_URL", "wss://voiceguide-fduoyoub.livekit.cloud")


@app.get("/")
@app.get("/api")
@app.get("/api/health")
@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint for Vercel deployment."""
    return {
        "status": "ok",
        "livekit_url": LIVEKIT_URL,
        "api_key_configured": str(bool(LIVEKIT_API_KEY)),
    }


@app.get("/api/token")
@app.get("/token")
def get_token(
    room: str = Query(default="voiceguide-room"),
    identity: Optional[str] = Query(default=None),
) -> dict:
    """Issue a LiveKit JWT token for frontend WebRTC connection."""
    participant_id = identity if identity and identity.strip() else f"user-{uuid.uuid4().hex[:6]}"

    if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
        return {
            "error": "LIVEKIT_API_KEY or LIVEKIT_API_SECRET is not configured in Vercel Environment Variables.",
            "token": "",
            "url": LIVEKIT_URL,
            "room": room,
            "identity": participant_id,
        }

    grant = VideoGrants(
        room_join=True,
        room=room,
        can_publish=True,
        can_subscribe=True,
        can_publish_data=True,
    )

    token = (
        AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        .with_identity(participant_id)
        .with_name(participant_id)
        .with_grants(grant)
        .to_jwt()
    )

    return {
        "token": token,
        "url": LIVEKIT_URL,
        "room": room,
        "identity": participant_id,
    }
