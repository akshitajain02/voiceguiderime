"""Local mock WebSocket server simulating Rime's /ws3 TTS API."""

import asyncio
import base64
import json
import logging
from typing import Optional

import websockets

logger = logging.getLogger("mock_rime_server")


class MockRimeServer:
    """Mock WebSocket server replicating Rime's /ws3 streaming protocol."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8765,
        expected_token: Optional[str] = "test-token",
        num_chunks: int = 3,
        chunk_size: int = 512,
    ):
        self.host = host
        self.port = port
        self.expected_token = expected_token
        self.num_chunks = num_chunks
        self.chunk_size = chunk_size
        self._server = None

    async def _handler(self, websocket):
        """Handle incoming WebSocket connection and requests."""
        # Extract headers from the connection request
        headers = getattr(websocket, "request_headers", None)
        if headers is None and hasattr(websocket, "request"):
            headers = websocket.request.headers

        auth_header = headers.get("Authorization", "") if headers else ""

        if self.expected_token is not None:
            expected_header = f"Bearer {self.expected_token}"
            if auth_header != expected_header:
                logger.warning(f"Unauthorized connection attempt: {auth_header}")
                await websocket.send(json.dumps({"error": "Unauthorized: Invalid or missing API key"}))
                await websocket.close(code=4401, reason="Unauthorized")
                return

        try:
            async for message in websocket:
                try:
                    payload = json.loads(message)
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({"error": "Invalid JSON format"}))
                    continue

                text = payload.get("text", "")
                logger.info(f"Mock server received text: {text!r}")

                # Simulate audio streaming in multiple chunks
                for i in range(self.num_chunks):
                    await asyncio.sleep(0.02)  # Simulate network/synthesis latency
                    # Create dummy audio frame bytes
                    dummy_audio = (f"[AUDIO_CHUNK_{i+1}_FOR:{text[:10]}]".encode() * (self.chunk_size // 20))[:self.chunk_size]
                    b64_audio = base64.b64encode(dummy_audio).decode("utf-8")
                    await websocket.send(json.dumps({
                        "audio": b64_audio,
                        "chunk_index": i,
                    }))

                # Send End of Stream
                await websocket.send(json.dumps({"type": "eos"}))

        except websockets.exceptions.ConnectionClosed:
            logger.info("Client disconnected from mock server.")

    async def start(self):
        """Start the mock server."""
        self._server = await websockets.serve(self._handler, self.host, self.port)
        logger.info(f"Mock Rime WebSocket server running at ws://{self.host}:{self.port}")

    async def stop(self):
        """Stop the mock server."""
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
            logger.info("Mock Rime WebSocket server stopped.")

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    server = MockRimeServer()

    async def main():
        await server.start()
        print(f"Mock server running on ws://{server.host}:{server.port}/ws3. Press Ctrl+C to stop.")
        try:
            await asyncio.Future()  # run forever
        except KeyboardInterrupt:
            await server.stop()

    asyncio.run(main())
