from __future__ import annotations

import pytest

from windows_mic_client.orchestrator.fallback import ClientFallbackHandler


class FakePlayer:
    def __init__(self):
        self.played_files = []

    def play_file(self, path):
        self.played_files.append(path)


@pytest.mark.parametrize("event_name", ["server_not_found", "bad_audio"])
def test_fallback_handler_plays_expected_event_file(event_name):
    player = FakePlayer()
    handler = ClientFallbackHandler(player)
    handler.fallback_path = "assets/fallback_audio"

    handler.handle(event_name)

    assert player.played_files == [f"assets/fallback_audio/{event_name}.wav"]


def test_fallback_handler_rejects_unknown_event_without_playing():
    player = FakePlayer()
    handler = ClientFallbackHandler(player)

    with pytest.raises(ValueError, match="Unknown event name"):
        handler.handle("network_wobbled")

    assert player.played_files == []
