from __future__ import annotations

from typing import Any

import requests

from ..core.logging import get_logger
from ..utils.latency_logger import log_latency

logger = get_logger(__name__)


class AssistantAPIClient:
    def __init__(self, base_url: str, timeout_seconds: float = 300.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def health(self) -> dict[str, Any]:
        logger.info("api_request_started | endpoint=/health")
        with log_latency(logger, "api_request_completed", endpoint="/health"):
            response = requests.get(
                f"{self.base_url}/health",
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            return response.json()

    def transcribe(self, audio_bytes: bytes, session_id: str | None) -> dict[str, Any]:
        """Transcribes audio bytes into text using piper python API"""
        logger.info(f"api_request_started | endpoint=/transcribe session_id={session_id}")
        with log_latency(
            logger, "api_request_completed", endpoint="/transcribe", session_id=session_id
        ):
            files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
            data = {"session_id": session_id}

            response = requests.post(
                f"{self.base_url}/transcribe",
                files=files,
                data=data,
                timeout=self.timeout_seconds,
            )

            return response.json()

    def synthesize(self, text: str, session_id: str | None) -> Any:
        logger.info(f"api_request_started | endpoint=/synthesize session_id={session_id}")
        with log_latency(
            logger, "api_request_completed", endpoint="/synthesize", session_id=session_id
        ):
            payload = {"text": text, "session_id": session_id}
            response = requests.post(
                f"{self.base_url}/synthesize",
                json=payload,
                timeout=self.timeout_seconds,
                stream=True,
            )
            resolved_id = response.headers.get("X-Session-ID")
            return response, resolved_id

    def speak(self, audio_bytes: bytes, session_id: str | None) -> Any:
        """Runs full pipeline on endpoint"""
        logger.info(f"api_request_started | endpoint=/speak session_id={session_id}")
        with log_latency(logger, "api_request_completed", endpoint="/speak", session_id=session_id):
            files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
            data = {"session_id": session_id}

            response = requests.post(
                f"{self.base_url}/speak",
                files=files,
                data=data,
                timeout=self.timeout_seconds,
            )
            resolved_id = response.headers.get("X-Session-ID")

            try:
                fallback_text = response.headers.get("X-Fallback-TXT")
                logger.info(f"Fallback_text | {fallback_text}")
            except:
                pass

            return response, resolved_id
