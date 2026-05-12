from __future__ import annotations

from types import SimpleNamespace

from windows_mic_client import main as main_module
from windows_mic_client.orchestrator.fallback import ClientFallbackHandler
from windows_mic_client.orchestrator.orchestrator import ClientOrchestrator


class FlowAPI:
    def __init__(self):
        self.calls = []

    def health(self):
        self.calls.append(("health",))
        return True

    def speak(self, audio_bytes, session_id):
        self.calls.append(("speak", audio_bytes, session_id))
        return ["chunk-1", "chunk-2"], "session-123"

    def wake_server(self):
        self.calls.append(("wake_server",))

    def close_server(self):
        self.calls.append(("close_server",))


class FlowPlayer:
    def __init__(self):
        self.streams = []
        self.files = []
        self.stopped = False

    def play_wav_stream(self, stream):
        self.streams.append(stream)

    def play_file(self, path):
        self.files.append(path)

    def stop_playback(self):
        self.stopped = True


def test_orchestrator_speak_then_fallback_share_player_boundary():
    api = FlowAPI()
    player = FlowPlayer()
    fallback = ClientFallbackHandler(player)
    fallback.fallback_path = "assets/fallback_audio"
    orchestrator = ClientOrchestrator(api, player, fallback)

    orchestrator.speak(b"wav")
    orchestrator.handle("server_not_found")

    assert api.calls == [("speak", b"wav", None)]
    assert player.streams == [["chunk-1", "chunk-2"]]
    assert player.files == ["assets/fallback_audio/server_not_found.wav"]
    assert orchestrator.session_id == "session-123"


def test_run_wires_components_and_starts_controller_on_healthy_server(monkeypatch):
    constructed = {}
    settings = SimpleNamespace(
        assistant_api_base_url="http://assistant.test",
        assistant_api_timeout_seconds=8.0,
        mic_sample_rate=16_000,
        mic_channels=1,
        mic_block_size=512,
    )

    class FakeAPI:
        def __init__(self, base_url, timeout_seconds):
            constructed["api_args"] = (base_url, timeout_seconds)

    class FakePlayer:
        def __init__(self):
            constructed["player"] = self

    class FakeFallback:
        def __init__(self, player):
            constructed["fallback_player"] = player

    class FakeOrchestrator:
        def __init__(self, api, player, fallback_handler):
            constructed["orchestrator_args"] = (api, player, fallback_handler)

        def health_check(self):
            constructed["health_checked"] = True
            return True

        def synthesize(self, text):
            constructed["synthesized"] = text

    class FakeRecorder:
        def __init__(self, sample_rate, channels, block_size):
            constructed["recorder_args"] = (sample_rate, channels, block_size)
            constructed["recorder"] = self

    class FakeController:
        def __init__(self, recorder, orchestrator):
            constructed["controller_args"] = (recorder, orchestrator)
            constructed["controller"] = self

    monkeypatch.setattr(main_module, "get_client_settings", lambda: settings)
    monkeypatch.setattr(main_module, "AssistantAPIClient", FakeAPI)
    monkeypatch.setattr(main_module, "AudioPlayer", FakePlayer)
    monkeypatch.setattr(main_module, "ClientFallbackHandler", FakeFallback)
    monkeypatch.setattr(main_module, "ClientOrchestrator", FakeOrchestrator)
    monkeypatch.setattr(main_module, "MicrophoneRecorder", FakeRecorder)
    monkeypatch.setattr(main_module, "PushToTalkController", FakeController)

    main_module.run()

    assert constructed["api_args"] == ("http://assistant.test", 8.0)
    assert constructed["fallback_player"] is constructed["player"]
    assert constructed["health_checked"] is True
    assert constructed["synthesized"] == "Alfred Awake."
    assert constructed["recorder_args"] == (16_000, 1, 512)
    recorder, orchestrator = constructed["controller_args"]
    assert recorder is constructed["recorder"]
    assert orchestrator.__class__ is FakeOrchestrator
