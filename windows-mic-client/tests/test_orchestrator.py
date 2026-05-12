from __future__ import annotations

from windows_mic_client.orchestrator.orchestrator import ClientOrchestrator


class FakeAPI:
    def __init__(self):
        self.calls = []
        self.health_response = True

    def health(self):
        self.calls.append(("health",))
        return self.health_response

    def wake_server(self):
        self.calls.append(("wake_server",))

    def close_server(self):
        self.calls.append(("close_server",))

    def speak(self, audio_bytes, session_id):
        self.calls.append(("speak", audio_bytes, session_id))
        return "audio-response", "resolved-session"

    def transcribe(self, audio_bytes, session_id):
        self.calls.append(("transcribe", audio_bytes, session_id))
        return {"text": "hello"}

    def synthesize(self, text, session_id):
        self.calls.append(("synthesize", text, session_id))
        return "synth-response", "synth-session"


class FakePlayer:
    def __init__(self):
        self.played_streams = []
        self.stopped = False

    def play_wav_stream(self, response):
        self.played_streams.append(response)

    def stop_playback(self):
        self.stopped = True


class FakeFallbackHandler:
    def __init__(self):
        self.handled = []

    def handle(self, event_name):
        self.handled.append(event_name)


def make_orchestrator():
    api = FakeAPI()
    player = FakePlayer()
    fallback = FakeFallbackHandler()
    return ClientOrchestrator(api, player, fallback), api, player, fallback


def test_session_id_setter_preserves_existing_session_and_handles_falsy_values():
    orchestrator, _, _, _ = make_orchestrator()

    orchestrator.session_id = ""
    assert orchestrator.session_id is None

    orchestrator.session_id = 123
    assert orchestrator.session_id is None

    orchestrator.session_id = "session-1"
    orchestrator.session_id = "session-2"
    assert orchestrator.session_id == "session-1"


def test_speak_calls_api_with_none_session_plays_response_and_stores_resolved_id():
    orchestrator, api, player, _ = make_orchestrator()

    orchestrator.speak(b"audio")

    assert api.calls == [("speak", b"audio", None)]
    assert player.played_streams == ["audio-response"]
    assert orchestrator.session_id == "resolved-session"


def test_synthesize_calls_api_plays_response_and_stores_session():
    orchestrator, api, player, _ = make_orchestrator()

    orchestrator.synthesize("Alfred awake.")

    assert api.calls == [("synthesize", "Alfred awake.", None)]
    assert player.played_streams == ["synth-response"]
    assert orchestrator.session_id == "synth-session"


def test_server_and_fallback_boundaries_delegate_to_dependencies():
    orchestrator, api, player, fallback = make_orchestrator()

    assert orchestrator.health_check() is True
    orchestrator.wake_server()
    orchestrator.close_server()
    orchestrator.handle("server_not_found")
    orchestrator.stop_speech()

    assert api.calls == [("health",), ("wake_server",), ("close_server",)]
    assert fallback.handled == ["server_not_found"]
    assert player.stopped is True
