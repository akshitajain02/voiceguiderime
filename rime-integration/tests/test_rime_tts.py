"""Unit and integration tests for Rime WebSocket TTS."""

import asyncio
import os
import sys
from pathlib import Path
import pytest

# Ensure parent directory is in sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import RimeConfig
from client import RimeTTSClient, RimeTTSError, RimeAuthenticationError
from mock_server import MockRimeServer


def test_config_builder():
    """Verify URL generation with parameters."""
    cfg = RimeConfig(
        api_key="test-key",
        speaker="eleanor",
        model_id="mistv3",
        audio_format="mp3",
        ws_url="wss://users-ws.rime.ai/ws3",
        time_scale_factor=1.2,
    )
    url = cfg.build_connection_url()
    assert url.startswith("wss://users-ws.rime.ai/ws3?")
    assert "speaker=eleanor" in url
    assert "modelId=mistv3" in url
    assert "audioFormat=mp3" in url
    assert "timeScaleFactor=1.2" in url


def test_config_from_env(monkeypatch):
    """Verify loading configuration from environment."""
    monkeypatch.setenv("RIME_API_KEY", "env-secret-token")
    monkeypatch.setenv("RIME_SPEAKER", "cove")
    monkeypatch.setenv("RIME_MODEL_ID", "coda")
    monkeypatch.setenv("RIME_AUDIO_FORMAT", "pcm")
    monkeypatch.setenv("RIME_TIME_SCALE_FACTOR", "0.95")

    cfg = RimeConfig.from_env()
    assert cfg.api_key == "env-secret-token"
    assert cfg.speaker == "cove"
    assert cfg.model_id == "coda"
    assert cfg.audio_format == "pcm"
    assert cfg.time_scale_factor == 0.95


@pytest.mark.asyncio
async def test_client_not_connected_error():
    """Verify error when client methods are called without connect()."""
    client = RimeTTSClient(RimeConfig(api_key="key"))
    with pytest.raises(RimeTTSError, match="not connected"):
        await client.send_text("Hello")

    with pytest.raises(RimeTTSError, match="not connected"):
        async for _ in client.stream_audio():
            pass


@pytest.mark.asyncio
async def test_client_mock_streaming():
    """Test streaming text and receiving audio chunks using MockRimeServer."""
    test_port = 8766
    server = MockRimeServer(
        host="127.0.0.1",
        port=test_port,
        expected_token="valid-token",
        num_chunks=4,
        chunk_size=256,
    )

    async with server:
        config = RimeConfig(
            api_key="valid-token",
            ws_url=f"ws://127.0.0.1:{test_port}/ws3",
            speaker="cove",
            model_id="mistv3",
            audio_format="mp3",
        )

        async with RimeTTSClient(config) as client:
            chunks = []
            async for chunk in client.synthesize("Testing voice synthesis."):
                chunks.append(chunk)

            assert len(chunks) == 4
            assert all(len(c) == 256 for c in chunks)
            assert client.last_ttfb is not None
            assert client.last_ttfb > 0


@pytest.mark.asyncio
async def test_client_synthesize_to_bytes():
    """Test convenience helper synthesize_to_bytes()."""
    test_port = 8767
    server = MockRimeServer(
        host="127.0.0.1",
        port=test_port,
        expected_token="valid-token",
        num_chunks=3,
        chunk_size=100,
    )

    async with server:
        config = RimeConfig(
            api_key="valid-token",
            ws_url=f"ws://127.0.0.1:{test_port}/ws3",
        )

        async with RimeTTSClient(config) as client:
            audio_data = await client.synthesize_to_bytes("Quick brown fox.")
            assert len(audio_data) == 300


@pytest.mark.asyncio
async def test_client_unauthorized():
    """Test handling of invalid token / unauthorized connection."""
    test_port = 8768
    server = MockRimeServer(
        host="127.0.0.1",
        port=test_port,
        expected_token="secret-key",
    )

    async with server:
        config = RimeConfig(
            api_key="wrong-key",
            ws_url=f"ws://127.0.0.1:{test_port}/ws3",
        )

        async with RimeTTSClient(config) as client:
            with pytest.raises((RimeAuthenticationError, RimeTTSError)):
                async for _ in client.synthesize("Should fail auth"):
                    pass
