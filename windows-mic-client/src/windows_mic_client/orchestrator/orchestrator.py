from typing import Any

from ..audio.player import AudioPlayer
from ..client.assistant_api_client import AssistantAPIClient
from ..core.logging import get_logger
from ..utils.latency_logger import log_latency
from .fallback import ClientFallbackHandler

logger = get_logger(__name__)


class ClientOrchestrator:
    def __init__(
        self, api: AssistantAPIClient, player: AudioPlayer, fallback_handler: ClientFallbackHandler
    ) -> None:
        self.api = api
        self.player = player
        self.fallback_handler = fallback_handler

        self.__session_id = None

    # Getter, setter, deleter for session_id
    @property
    def session_id(self) -> str | None:
        return self.__session_id

    @session_id.setter
    def session_id(self, value: str) -> None:
        if not isinstance(value, str):
            logger.error("Tried to write non-string to session id")
        elif self.__session_id is not None and self.__session_id != value:
            logger.error("Attempted overwrite of existing session_id")
        elif not value:
            logger.warning("Session ID was a falsy string, setting to None")
            self.__session_id = None
        else:
            # Either id is currently None or new value is same as current
            self.__session_id = value

    @session_id.deleter
    def session_id(self) -> None:
        self.__session_id = None

    # Stop current speech by raising flag in speaker, to be used by push-to-talk
    def stop_speech(self):
        self.player.stop_playback()

    def health_check(self) -> dict[str, Any]:
        response_json = self.api.health()
        logger.info(f"health_response | response={response_json}")

    def speak(self, audio_bytes: bytes):
        logger.info(f"interaction_started | session_id={self.session_id}")
        with log_latency(logger, "interaction_completed", session_id=self.session_id):
            response, ressolved_id = self.api.speak(audio_bytes, self.session_id)

            with log_latency(logger, "playback_completed", session_id=ressolved_id):
                logger.info(f"playback_started | session_id={ressolved_id}")
                self.player.play_wav_stream(response)

            self.session_id = ressolved_id
            logger.info(f"session_id_resolved | session_id={self.session_id}")

    def transcribe(self, audio_bytes: bytes):
        response_json = self.api.transcribe(audio_bytes, self.session_id)
        logger.info(f"transcribe_response | response={response_json}")

    def synthesize(self, text: str) -> None:
        logger.info(f"interaction_started | session_id={self.session_id}")
        with log_latency(logger, "interaction_completed", session_id=self.session_id):
            iter_response, resolved_session_id = self.api.synthesize(text, self.session_id)
            with log_latency(logger, "playback_completed", session_id=resolved_session_id):
                logger.info(f"playback_started | session_id={resolved_session_id}")
                self.player.play_wav_stream(iter_response)
            self.session_id = resolved_session_id

    def handle(self, event_name: str) -> None:
        self.fallback_handler.handle(event_name)
