from __future__ import annotations

from typing import Any

import requests

from ..core.logging import get_logger
from ..utils.latency_logger import log_latency
from ..core.config import get_client_settings

logger = get_logger(__name__)
settings = get_client_settings()


class AssistantAPIClient:
    def __init__(self, base_url: str, timeout_seconds: float = 300.0) -> None:
        self.base_url = settings.assistant_api_base_url.rstrip("/")
        self.lifecycle_manager_base_url = settings.lifecycle_manager_base_url.rstrip(
            "/"
        )
        self.timeout_seconds = settings.assistant_api_timeout_seconds

    def health(self) -> bool:
        logger.info("get /health started | endpoint=/health")
        with log_latency(logger, "get /health completed"):
            try:
                response = requests.get(
                    f"{self.base_url}/health",
                    timeout=self.timeout_seconds,
                )
            except Exception as e:
                logger.warning(f"health failed | exc={e}")
                return False
            else:
                response_json = response.json()
                status = str(response_json.get("status"))
                logger.info(f"health response recieved | status={status}")
                return status == "ok"

    def wake_server(self) -> None:
        requests.post(
            f"{self.lifecycle_manager_base_url}/services/local-assistant-server/start"
        )

    def close_server(self) -> None:
        requests.post(
            f"{self.lifecycle_manager_base_url}/services/local-assistant-server/stop"
        )

    def transcribe(self, audio_bytes: bytes, session_id: str | None) -> dict[str, Any]:
        """Transcribes audio bytes into text using piper python API"""
        logger.info(
            f"api_request_started | endpoint=/transcribe session_id={session_id}"
        )
        with log_latency(
            logger,
            "api_request_completed",
            endpoint="/transcribe",
            session_id=session_id,
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
        logger.info(
            f"api_request_started | endpoint=/synthesize session_id={session_id}"
        )
        with log_latency(
            logger,
            "api_request_completed",
            endpoint="/synthesize",
            session_id=session_id,
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
        with log_latency(
            logger, "api_request_completed", endpoint="/speak", session_id=session_id
        ):
            files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
            data = {"session_id": session_id}

            response = requests.post(
                f"{self.base_url}/speak",
                files=files,
                data=data,
                timeout=self.timeout_seconds,
                stream=True,
            )
            resolved_id = response.headers.get("X-Session-ID")

            try:
                fallback_text = response.headers.get("X-Fallback-TXT")
                logger.info(f"Fallback_text | {fallback_text}")
            except Exception:
                pass

            return response, resolved_id
