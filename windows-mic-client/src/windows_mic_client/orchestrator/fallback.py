from ..audio.player import AudioPlayer
from ..core.config import get_client_settings
from ..core.logging import get_logger

settings = get_client_settings()
logger = get_logger(__name__)


class ClientFallbackHandler:
    """Fallback handler for graceful degredation whenever a pipeline module fails.
    Plays message"""

    def __init__(self, player: AudioPlayer):
        self.player = player
        self.fallback_path = settings.fallback_path
        self.fallback_events = {"server_not_found", "bad_audio"}

    def handle(self, event_name: str) -> None:
        if event_name not in self.fallback_events:
            logger.error(f"unknown event_name | event_name={event_name}")
            raise ValueError("Unknown event name, should be 'server_not_found' or 'bad_audio'")

        resolved_path = self.fallback_path + "/" + event_name + ".wav"

        logger.info(f"Fallback_played | event_name={event_name}")
        self.player.play_file(resolved_path)
