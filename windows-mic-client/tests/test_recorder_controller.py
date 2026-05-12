from __future__ import annotations

import numpy as np

from windows_mic_client.audio import recorder as recorder_module
from windows_mic_client.audio.recorder import MicrophoneRecorder, PushToTalkController


class NonBlockingPushToTalkController(PushToTalkController):
    def listen_for_keypresses(self):
        return None


class FakeRecorder:
    def __init__(self, audio_bytes):
        self.audio_bytes = audio_bytes
        self.started = False
        self.stopped = False

    def start(self):
        self.started = True

    def stop(self):
        self.stopped = True
        return self.audio_bytes


class FakeOrchestrator:
    def __init__(self):
        self.stopped_speech = False
        self.spoken = []
        self.handled = []
        self.closed = False

    def stop_speech(self):
        self.stopped_speech = True

    def speak(self, audio_bytes):
        self.spoken.append(audio_bytes)

    def handle(self, event_name):
        self.handled.append(event_name)

    def close_server(self):
        self.closed = True


def test_microphone_callback_copies_frames():
    recorder = MicrophoneRecorder(sample_rate=16_000, channels=1, block_size=4)
    frame = np.array([[1], [2]], dtype=np.int16)

    recorder._callback(frame, frames=2, time=None, status=None)
    frame[0][0] = 99

    assert recorder.frames[0].tolist() == [[1], [2]]


def test_microphone_stop_returns_none_when_no_frames():
    recorder = MicrophoneRecorder(sample_rate=16_000, channels=1, block_size=4)

    assert recorder.stop() is None


def test_microphone_record_uses_sounddevice_and_converts_to_wav(monkeypatch):
    captured = {}

    def fake_rec(frames, samplerate, channels, dtype):
        captured.update(
            frames=frames,
            samplerate=samplerate,
            channels=channels,
            dtype=dtype,
        )
        return np.array([[0], [100]], dtype=np.int16)

    monkeypatch.setattr(recorder_module.sd, "rec", fake_rec)
    monkeypatch.setattr(
        recorder_module.sd, "wait", lambda: captured.update(waited=True)
    )

    result = MicrophoneRecorder(sample_rate=10, channels=1, block_size=4).record(
        max_duration=0.2
    )

    assert result.startswith(b"RIFF")
    assert captured == {
        "frames": 2,
        "samplerate": 10,
        "channels": 1,
        "dtype": "int16",
        "waited": True,
    }


def test_push_to_talk_starts_recording_on_space():
    recorder = FakeRecorder(audio_bytes=b"")
    orchestrator = FakeOrchestrator()
    controller = NonBlockingPushToTalkController(recorder, orchestrator)

    controller.start_recording(recorder_module.keyboard.Key.space)

    assert controller.is_recording is True
    assert recorder.started is True
    assert orchestrator.stopped_speech is True


def test_push_to_talk_routes_missing_or_too_short_audio_to_bad_audio():
    for audio_bytes in (None, b"x" * 1024):
        recorder = FakeRecorder(audio_bytes=audio_bytes)
        orchestrator = FakeOrchestrator()
        controller = NonBlockingPushToTalkController(recorder, orchestrator)
        controller.is_recording = True

        controller.stop_recording(recorder_module.keyboard.Key.space)

        assert recorder.stopped is True
        assert orchestrator.handled == ["bad_audio"]
        assert orchestrator.spoken == []


def test_push_to_talk_sends_valid_audio_to_orchestrator():
    recorder = FakeRecorder(audio_bytes=b"x" * 1025)
    orchestrator = FakeOrchestrator()
    controller = NonBlockingPushToTalkController(recorder, orchestrator)
    controller.is_recording = True

    controller.stop_recording(recorder_module.keyboard.Key.space)

    assert recorder.stopped is True
    assert orchestrator.handled == []
    assert orchestrator.spoken == [b"x" * 1025]
