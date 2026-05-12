from __future__ import annotations
import time

from .audio.player import AudioPlayer
from .audio.recorder import MicrophoneRecorder, PushToTalkController
from .client.assistant_api_client import AssistantAPIClient
from .core.config import get_client_settings
from .core.logging import get_logger
from .orchestrator.fallback import ClientFallbackHandler
from .orchestrator.orchestrator import ClientOrchestrator

import os

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
    # NOTE Replace ugly logic with helper:

    try:
        if not orchestrator.health_check():
            orchestrator.wake_server()
            for i in range(15):
                if i == 14:
                    raise SystemError("Startup failed | timed out ")
                if not orchestrator.health_check():
                    time.sleep(3)
                else:
                    break

    except Exception as e:
        logger.warning(f"run failed | Server not found: {e}")
        orchestrator.handle("server_not_found")

        # NOTE check if valid exit strategy
        time.sleep(5)
        os._exit(1)
    else:
        orchestrator.synthesize("Alfred Awake.")

    # Initialise input/control layer
    PushToTalkController(
        MicrophoneRecorder(
            sample_rate=settings.mic_sample_rate,
            channels=settings.mic_channels,
            block_size=settings.mic_block_size,
        ),
        orchestrator=orchestrator,
    )


if __name__ == "__main__":
    run()
