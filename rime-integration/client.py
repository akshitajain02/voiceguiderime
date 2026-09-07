"""Asynchronous streaming WebSocket client for Rime Text-to-Speech (TTS)."""

import asyncio
import base64
import json
import logging
import time
from typing import AsyncIterator, Dict, Optional

import websockets
from websockets.exceptions import ConnectionClosed

from config import RimeConfig

logger = logging.getLogger("rime_tts")


class RimeTTSError(Exception):
    """Base exception for Rime TTS client errors."""
    pass


class RimeAuthenticationError(RimeTTSError):
    """Raised when authentication with Rime API fails."""
    pass


class RimeTTSClient:
    """Streaming WebSocket client for Rime TTS /ws3 endpoint."""

    def __init__(self, config: Optional[RimeConfig] = None):
        self.config = config or RimeConfig.from_env()
        self.websocket = None
        self._last_send_time: Optional[float] = None
        self.last_ttfb: Optional[float] = None

    async def connect(self):
        """Establish the WebSocket connection to Rime."""
        url = self.config.build_connection_url()
        headers: Dict[str, str] = {}

        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        logger.info(f"Connecting to Rime WebSocket at {url}")

        try:
            # websockets >= 14 / 13 uses additional_headers, older versions use extra_headers
            try:
                self.websocket = await websockets.connect(
                    url,
                    additional_headers=headers,
                )
            except TypeError:
                self.websocket = await websockets.connect(
                    url,
                    extra_headers=headers,
                )
            logger.info("Successfully connected to Rime WebSocket.")
        except Exception as exc:
            logger.error(f"Failed to connect to Rime WebSocket: {exc}")
            raise RimeTTSError(f"Connection failed: {exc}") from exc

    async def close(self):
        """Close the WebSocket connection."""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            logger.info("Rime WebSocket connection closed.")

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def send_text(self, text: str):
        """Send a text fragment to Rime for synthesis."""
        if not self.websocket:
            raise RimeTTSError("WebSocket is not connected. Call connect() first.")

        payload = {"text": text}
        self._last_send_time = time.perf_counter()
        logger.debug(f"Sending text to Rime: {text!r}")
        try:
            await self.websocket.send(json.dumps(payload))
        except ConnectionClosed as exc:
            rcvd_reason = str(getattr(exc.rcvd, "reason", "")).lower()
            rcvd_code = getattr(exc.rcvd, "code", None)
            if rcvd_code == 4401 or "unauthorized" in rcvd_reason or "auth" in rcvd_reason:
                raise RimeAuthenticationError(f"Rime authentication error: {exc.rcvd.reason}") from exc
            raise RimeTTSError(f"Connection closed while sending text: {exc}") from exc
        except Exception as exc:
            raise RimeTTSError(f"Failed to send text: {exc}") from exc

    async def stream_audio(self) -> AsyncIterator[bytes]:
        """Receive and yield raw audio chunks until End of Stream (eos)."""
        if not self.websocket:
            raise RimeTTSError("WebSocket is not connected. Call connect() first.")

        first_chunk = True

        try:
            async for raw_message in self.websocket:
                # Some servers may send binary or json
                if isinstance(raw_message, bytes):
                    # Raw audio bytes directly
                    if first_chunk and self._last_send_time is not None:
                        self.last_ttfb = time.perf_counter() - self._last_send_time
                        first_chunk = False
                    yield raw_message
                    continue

                try:
                    data = json.loads(raw_message)
                except json.JSONDecodeError:
                    logger.warning(f"Received non-JSON text message: {raw_message}")
                    continue

                # Check for errors in server response
                if "error" in data:
                    error_msg = data.get("error")
                    if "auth" in str(error_msg).lower() or "unauthorized" in str(error_msg).lower():
                        raise RimeAuthenticationError(f"Rime authentication error: {error_msg}")
                    raise RimeTTSError(f"Rime API returned error: {error_msg}")

                # Check for base64 audio chunk
                if "audio" in data and data["audio"]:
                    if first_chunk and self._last_send_time is not None:
                        self.last_ttfb = time.perf_counter() - self._last_send_time
                        first_chunk = False
                        logger.info(f"Received first audio chunk. TTFB: {self.last_ttfb * 1000:.1f}ms")

                    audio_bytes = base64.b64decode(data["audio"])
                    yield audio_bytes

                # Check for End of Stream (EOS)
                if data.get("type") == "eos" or data.get("eos") is True:
                    logger.debug("Received End of Stream (EOS).")
                    break

        except ConnectionClosed as exc:
            rcvd_reason = str(getattr(exc.rcvd, "reason", "")).lower()
            rcvd_code = getattr(exc.rcvd, "code", None)
            if rcvd_code == 4401 or "unauthorized" in rcvd_reason or "auth" in rcvd_reason:
                raise RimeAuthenticationError(f"Rime authentication error: {exc.rcvd.reason}") from exc
            logger.info(f"WebSocket closed: {exc}")
        except Exception as exc:
            if not isinstance(exc, RimeTTSError):
                logger.error(f"Error while receiving audio stream: {exc}")
                raise RimeTTSError(f"Streaming error: {exc}") from exc
            raise

    async def synthesize(self, text: str) -> AsyncIterator[bytes]:
        """Convenience method: Send text and yield incoming audio chunks."""
        await self.send_text(text)
        async for chunk in self.stream_audio():
            yield chunk

    async def synthesize_to_bytes(self, text: str) -> bytes:
        """Convenience method: Synthesize text and return full audio bytes."""
        chunks = []
        async for chunk in self.synthesize(text):
            chunks.append(chunk)
        return b"".join(chunks)
