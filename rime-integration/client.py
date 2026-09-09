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
        """Send a text fragment to Rime for synthesis, then signal end-of-input."""
        if not self.websocket:
            raise RimeTTSError("WebSocket is not connected. Call connect() first.")

        payload = {"text": text}
        self._last_send_time = time.perf_counter()
        logger.debug(f"Sending text to Rime: {text!r}")
        try:
            await self.websocket.send(json.dumps(payload))
            # FIX: Rime's /ws3 protocol needs an explicit end-of-input signal
            # before it finalizes synthesis and sends EOS back. Without this,
            # stream_audio() waits forever for a final chunk/EOS that never arrives.
            await self.websocket.send(json.dumps({"operation": "eos"}))
        except ConnectionClosed as exc:
            rcvd_reason = str(getattr(exc.rcvd, "reason", "")).lower()
            rcvd_code = getattr(exc.rcvd, "code", None)
            if rcvd_code == 4401 or "unauthorized" in rcvd_reason or "auth" in rcvd_reason:
                raise RimeAuthenticationError(f"Rime authentication error: {exc.rcvd.reason}") from exc
            raise RimeTTSError(f"Connection closed while sending text: {exc}") from exc
        except Exception as exc:
            raise RimeTTSError(f"Failed to send text: {exc}") from exc

    async def stream_audio(self, timeout_seconds: float = 15.0) -> AsyncIterator[bytes]:
        """Receive and yield raw audio chunks until End of Stream (eos)."""
        if not self.websocket:
            raise RimeTTSError("WebSocket is not connected. Call connect() first.")

        first_chunk = True

        try:
            # FIX: wrap the receive loop with a timeout so a missing/late EOS
            # can't hang the whole program forever - it'll raise instead.
            async def _reader():
                nonlocal first_chunk
                async for raw_message in self.websocket:
                    if isinstance(raw_message, bytes):
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

                    if "error" in data:
                        error_msg = data.get("error")
                        if "auth" in str(error_msg).lower() or "unauthorized" in str(error_msg).lower():
                            raise RimeAuthenticationError(f"Rime authentication error: {error_msg}")
                        raise RimeTTSError(f"Rime API returned error: {error_msg}")

                    # FIX: Rime sends base64 audio under the "data" key when type == "chunk",
                    # NOT under an "audio" key. The old check ("audio" in data) never matched,
                    # so every chunk was silently skipped.
                    if data.get("type") == "chunk" and data.get("data"):
                        if first_chunk and self._last_send_time is not None:
                            self.last_ttfb = time.perf_counter() - self._last_send_time
                            first_chunk = False
                            logger.info(f"Received first audio chunk. TTFB: {self.last_ttfb * 1000:.1f}ms")

                        audio_bytes = base64.b64decode(data["data"])
                        yield audio_bytes

                    # FIX: Rime signals the end of the stream with {"type": "done"},
                    # not {"type": "eos"} / {"eos": true}. Kept the old check too in
                    # case a different model/version uses that shape.
                    if data.get("type") in ("done", "eos") or data.get("eos") is True:
                        logger.debug("Received End of Stream.")
                        break

            # Each "next chunk" wait is bounded - if Rime never sends EOS
            # (e.g. because we forgot to send our own eos signal), we fail
            # loudly after `timeout_seconds` instead of hanging silently.
            reader = _reader()
            while True:
                try:
                    chunk = await asyncio.wait_for(reader.__anext__(), timeout=timeout_seconds)
                except StopAsyncIteration:
                    break
                yield chunk

        except asyncio.TimeoutError:
            raise RimeTTSError(
                f"No audio/EOS received from Rime within {timeout_seconds}s. "
                "Did you forget to send the end-of-input signal after the text?"
            )
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