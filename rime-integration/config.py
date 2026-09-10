"""Configuration module for Rime WebSocket Streaming TTS."""

import os
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlencode, urlparse, urlunparse, parse_qsl

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


@dataclass
class RimeConfig:
    """Configuration settings for Rime Streaming TTS WebSocket connection."""

    api_key: str = ""
    speaker: str = "cove"
    model_id: str = "mistv3"
    audio_format: str = "mp3"
    ws_url: str = "wss://users-ws.rime.ai/ws3"
    time_scale_factor: Optional[float] = None
    speed_alpha: Optional[float] = None
    sampling_rate: Optional[int] = None
    lang: Optional[str] = None

    @classmethod
    def from_env(cls, env_path: Optional[str] = None) -> "RimeConfig":
        """Load configuration from environment variables or .env file."""
        if load_dotenv:
            load_dotenv(dotenv_path=env_path)

        def _get_float(key: str) -> Optional[float]:
            val = os.getenv(key)
            if val is not None and val.strip() != "":
                try:
                    return float(val.strip())
                except ValueError:
                    return None
            return None

        def _get_int(key: str) -> Optional[int]:
            val = os.getenv(key)
            if val is not None and val.strip() != "":
                try:
                    return int(val.strip())
                except ValueError:
                    return None
            return None

        return cls(
            api_key=os.getenv("RIME_API_KEY", "").strip(),
            speaker=os.getenv("RIME_SPEAKER", "cove").strip(),
            model_id=os.getenv("RIME_MODEL_ID", "mistv3").strip(),
            audio_format=os.getenv("RIME_AUDIO_FORMAT", "mp3").strip(),
            ws_url=os.getenv("RIME_WS_URL", "wss://users-ws.rime.ai/ws3").strip(),
            time_scale_factor=_get_float("RIME_TIME_SCALE_FACTOR"),
            speed_alpha=_get_float("RIME_SPEED_ALPHA"),
            sampling_rate=_get_int("RIME_SAMPLING_RATE"),
            lang=os.getenv("RIME_LANG"),
        )

    def build_connection_url(self) -> str:
        """Construct the full WebSocket URL including query parameters."""
        parsed = urlparse(self.ws_url)
        params = dict(parse_qsl(parsed.query))

        # Add configured parameters
        if self.speaker:
            params["speaker"] = self.speaker
        if self.model_id:
            params["modelId"] = self.model_id
        if self.audio_format:
            params["audioFormat"] = self.audio_format
        if self.time_scale_factor is not None:
            params["timeScaleFactor"] = str(self.time_scale_factor)
        if self.speed_alpha is not None:
            params["speedAlpha"] = str(self.speed_alpha)
        if self.sampling_rate is not None:
            params["samplingRate"] = str(self.sampling_rate)
        if self.lang:
            params["lang"] = self.lang

        new_query = urlencode(params)
        return urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment,
        ))
