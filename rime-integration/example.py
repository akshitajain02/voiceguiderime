"""Interactive and demonstration script for Rime TTS Streaming WebSocket."""

import argparse
import asyncio
import logging
import sys
import time
from pathlib import Path

from config import RimeConfig
from client import RimeTTSClient
from mock_server import MockRimeServer


async def run_demo(text: str, output_path: str, use_mock: bool = False, speaker: str = None, model: str = None):
    config = RimeConfig.from_env()

    if speaker:
        config.speaker = speaker
    if model:
        config.model_id = model

    mock_server = None
    if use_mock:
        print("\n[INFO] Starting local Mock Rime Server on ws://127.0.0.1:8765/ws3 ...")
        config.ws_url = "ws://127.0.0.1:8765/ws3"
        config.api_key = "test-token"
        mock_server = MockRimeServer(host="127.0.0.1", port=8765, expected_token="test-token")
        await mock_server.start()
    else:
        if not config.api_key:
            print("\n[ERROR] RIME_API_KEY is not set!")
            print("Please create a .env file in the rime-integration directory with:")
            print("  RIME_API_KEY=your_key_here")
            print("Or test with the offline mock server using the --mock flag:")
            print("  python example.py --mock\n")
            sys.exit(1)

    try:
        print(f"\nTarget Endpoint: {config.build_connection_url()}")
        print(f"Synthesizing text: \"{text}\"")
        print("Connecting to WebSocket...")

        start_time = time.perf_counter()
        total_bytes = 0
        chunk_count = 0
        chunks = []

        async with RimeTTSClient(config) as client:
            print("Sending text payload...")
            await client.send_text(text)

            print("Streaming audio chunks...")
            async for chunk in client.stream_audio():
                chunk_count += 1
                total_bytes += len(chunk)
                chunks.append(chunk)
                print(f"  Chunk #{chunk_count}: {len(chunk)} bytes received (TTFB: {client.last_ttfb * 1000:.1f}ms)")

        elapsed = time.perf_counter() - start_time
        print("\n--- Stream Complete ---")
        print(f"Total Chunks: {chunk_count}")
        print(f"Total Audio Size: {total_bytes:,} bytes")
        print(f"Total Elapsed Time: {elapsed:.2f}s")
        if client.last_ttfb is not None:
            print(f"Time-To-First-Byte (TTFB): {client.last_ttfb * 1000:.1f} ms")

        # Save audio output
        out_file = Path(output_path)
        with open(out_file, "wb") as f:
            for c in chunks:
                f.write(c)
        print(f"Saved audio output to: {out_file.resolve()}\n")

    finally:
        if mock_server:
            await mock_server.stop()


def main():
    parser = argparse.ArgumentParser(description="Rime Streaming WebSocket TTS Demo")
    parser.add_argument(
        "--text",
        default="Hello! Welcome to VoiceGuide. This is a real-time streaming audio test using Rime text to speech.",
        help="Text to synthesize",
    )
    parser.add_argument(
        "--output",
        default="output.mp3",
        help="Output audio file path",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run against local mock server instead of live Rime API",
    )
    parser.add_argument(
        "--speaker",
        default=None,
        help="Rime voice speaker name (e.g. cove, eleanor)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Rime model ID (e.g. mistv3, coda)",
    )

    args = parser.parse_args()
    asyncio.run(run_demo(
        text=args.text,
        output_path=args.output,
        use_mock=args.mock,
        speaker=args.speaker,
        model=args.model,
    ))


if __name__ == "__main__":
    main()
