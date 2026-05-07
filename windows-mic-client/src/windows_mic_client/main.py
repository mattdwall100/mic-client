from __future__ import annotations

from .audio.player import AudioPlayer
from .audio.recorder import MicrophoneRecorder, PushToTalkController
from .client.assistant_api_client import AssistantAPIClient
from .core.config import get_client_settings
from .core.logging import get_logger
from .orchestrator.fallback import ClientFallbackHandler
from .orchestrator.orchestrator import ClientOrchestrator

import os
import time

logger = get_logger(__name__)


def run() -> None:
    settings = get_client_settings()

    # Initialise Output layer objects according to settings
    api = AssistantAPIClient(
        base_url=settings.assistant_api_base_url,
        timeout_seconds=settings.assistant_api_timeout_seconds,
    )
    player = AudioPlayer()

    # Initialise fallback handler, which utilises the player
    handler = ClientFallbackHandler(player)

    # Initialise Orchestration layer
    orchestrator = ClientOrchestrator(api=api, player=player, fallback_handler=handler)

    # server health check
    try:
        orchestrator.health_check()
        orchestrator.synthesize("Alfred Awake.")
    except Exception as e:
        logger.warning(f"Health | Server not found: {e}")
        orchestrator.handle("server_not_found")

        # NOTE check if valid exit strategy
        time.sleep(5)
        os._exit(1)

    # Initialise input/control layer
    mic_controller = PushToTalkController(
        MicrophoneRecorder(
            sample_rate=settings.mic_sample_rate,
            channels=settings.mic_channels,
            block_size=settings.mic_block_size,
        ),
        orchestrator=orchestrator,
    )


if __name__ == "__main__":
    run()
