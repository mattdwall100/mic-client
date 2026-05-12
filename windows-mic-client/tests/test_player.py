from __future__ import annotations


from windows_mic_client.audio import player as player_module
from windows_mic_client.audio.player import AudioPlayer


def test_bytes_to_stream_chunks_audio_bytes():
    audio = b"abcdefghij"
    player = AudioPlayer()

    assert list(player.bytes_to_stream(audio, chunk_size=4)) == [
        b"abcd",
        b"efgh",
        b"ij",
    ]


def test_play_file_reads_audio_and_delegates_to_stream(tmp_path):
    wav_path = tmp_path / "fallback.wav"
    wav_path.write_bytes(b"0123456789")
    player = AudioPlayer()
    captured_chunks = []

    def fake_play_wav_stream(stream):
        captured_chunks.extend(stream)

    player.play_wav_stream = fake_play_wav_stream

    player.play_file(str(wav_path))

    assert captured_chunks == [b"0123456789"]


def test_play_wav_stream_writes_response_chunks_and_closes(monkeypatch):
    writes = []
    stream_events = []

    class FakeOutputStream:
        def __init__(self, **kwargs):
            stream_events.append(("init", kwargs))

        def start(self):
            stream_events.append(("start", None))

        def write(self, audio):
            writes.append(audio.tolist())

        def abort(self):
            stream_events.append(("abort", None))

        def close(self):
            stream_events.append(("close", None))

    class ImmediateThread:
        def __init__(self, target, daemon):
            self.target = target
            self.daemon = daemon

        def start(self):
            self.target()

    class FakeResponse:
        closed = False

        def iter_content(self, chunk_size):
            assert chunk_size == 8_820
            yield (1).to_bytes(2, "little", signed=True)
            yield b""
            yield (-2).to_bytes(2, "little", signed=True)

        def close(self):
            self.closed = True

    monkeypatch.setattr(player_module.sd, "OutputStream", FakeOutputStream)
    monkeypatch.setattr(player_module.threading, "Thread", ImmediateThread)
    response = FakeResponse()
    player = AudioPlayer(sample_rate=22_050)

    player.play_wav_stream(response)

    assert writes == [[1], [-2]]
    assert response.closed is True
    assert player.current_stream is None
    assert player._playing is False
    assert ("start", None) in stream_events
    assert ("abort", None) in stream_events
    assert ("close", None) in stream_events
