from __future__ import annotations

import io
import threading
from collections.abc import Iterable
from pathlib import Path

import numpy as np
import sounddevice as sd
import soundfile as sf
from fastapi.responses import StreamingResponse

from ..core.logging import get_logger

logger = get_logger(__name__)


class AudioPlayer:
    def __init__(self, sample_rate: int = 22050, channels: int = 1) -> None:
        self.sample_rate = sample_rate
        self.channels = channels
        self.stop_flag = threading.Event()
        self._playing = False

        self.current_stream = None

    def play_wav_bytes(self, audio_bytes: bytes) -> None:
        """Play the given audio bytes."""
        logger.info(f"playback_started | bytes={len(audio_bytes)}")
        audio_array, sr = sf.read(io.BytesIO(audio_bytes))
        sd.play(audio_array, sr)
        sd.wait()
        logger.info("playback_finished | status=completed")

    def play_file(self, output_path: str) -> None:
        output_path = Path(output_path)

        # If already playing audio, skip the fallback response and move on
        if self._playing:
            logger.log("fallback_failed | Couldnt play as audio was playing")
        else:
            # read fallback audio bytes
            with open(output_path, "rb") as f:
                audio_bytes = f.read()

            # turn to generator and wrap for play_wav_stream use (interruptable)
            audio_stream = self.bytes_to_stream(audio_bytes)
            self.play_wav_stream(audio_stream)

    def play_wav_stream(self, response: StreamingResponse | Iterable[bytes]) -> None:
        self.stop_flag.clear()

        # chunk generator
        block_seconds = 0.2  # number of seconds of audio
        block_frames = int(self.sample_rate * block_seconds)
        block_bytes = block_frames * 2  # int16 mono: 2 bytes per frame

        # NOTE Can probably get rid of now, since have FallbackAudioStream object
        try:
            chunk_iterator = response.iter_content(chunk_size=block_bytes)
        except:
            chunk_iterator = response

        def _play_callback():
            self.current_stream = sd.OutputStream(
                samplerate=self.sample_rate, channels=1, dtype="int16"
            )
            self.current_stream.start()
            logger.info("playback_started | type=stream")

            try:
                # Writes chunks to stream until stopped
                for chunk in chunk_iterator:
                    if self.stop_flag.is_set():
                        logger.info("playback_finished | status=interrupted")
                        break
                    elif not chunk:
                        continue
                    else:
                        audio = np.frombuffer(chunk, dtype="int16")
                        self.current_stream.write(audio)
            finally:
                response.close()  # Closes the HTTP stream, to save bandwidth
                try:
                    if self.current_stream:
                        self.current_stream.abort()
                        self.current_stream.close()
                finally:
                    self._playing = False
                    self.current_stream = None
                    logger.info("playback_finished | status=completed")

        if not self._playing:
            self._playing = True
            threading.Thread(target=_play_callback, daemon=True).start()

    def stop_playback(self):
        self.stop_flag.set()

    def bytes_to_stream(self, audio_bytes: bytes, chunk_size: int = 4096):
        for i in range(0, len(audio_bytes), chunk_size):
            yield audio_bytes[i : i + chunk_size]
