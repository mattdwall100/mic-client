from __future__ import annotations

import sys

import numpy as np
import sounddevice as sd
from pynput import keyboard

from ..core.logging import get_logger
from ..orchestrator.orchestrator import ClientOrchestrator
from .audio_utils import numpy_to_wav_bytes

logger = get_logger(__name__)


class MicrophoneRecorder:
    """Controls recording using sounddevice"""

    def __init__(self, sample_rate: int, channels: int, block_size: int) -> None:
        self.sample_rate = sample_rate
        self.channels = channels
        self.block_size = block_size
        self.frames = []
        self.stream = None

    def _callback(self, indata, frames, time, status):
        if status:
            logger.warning(f"recorder_status | status={status}")
        self.frames.append(indata.copy())

    def start(self):
        # New recording with fresh frames list
        self.frames = []
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            blocksize=self.block_size,
            dtype="int16",
            callback=self._callback,
        )
        self.stream.start()

    def stop(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        if self.frames:
            audio_array = np.concatenate(self.frames)
            audio_bytes = numpy_to_wav_bytes(audio_array, self.sample_rate)
            return audio_bytes
        else:
            logger.warning("recorder_stopped | reason=no_frame_data_found")
            return None

    def record(self, max_duration: float, wait: bool = True) -> bytes:
        """Record audio for a specified duration and return the audio data as bytes."""
        audio = sd.rec(
            int(max_duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="int16",
        )
        logger.info(f"recording_started | max_duration={max_duration}")
        if wait:
            sd.wait()  # Wait until max wait time is finished
        # turn to wav bytes before returning to controller and orchestrator and then api
        audio_bytes = numpy_to_wav_bytes(np.asarray(audio, dtype="int16"), self.sample_rate)
        logger.info(f"recording_stopped | bytes_recorded={len(audio_bytes)}")
        return audio_bytes


class PushToTalkController:
    """Push to talk controls handler for MicrophoneRecorder"""

    def __init__(self, recorder: MicrophoneRecorder, orchestrator: ClientOrchestrator):
        self.recorder = recorder
        self.orchestrator = orchestrator
        self.is_recording = False

        self.listen_for_keypresses()

    def start_recording(self, key) -> None:
        if key == keyboard.Key.space and not self.is_recording:
            self.is_recording = True
            self.orchestrator.stop_speech()
            logger.info("recording_started | mode=push_to_talk")
            self.recorder.start()

    def stop_recording(self, key) -> None:
        if key == keyboard.Key.space and self.is_recording:
            self.is_recording = False
            audio_bytes = self.recorder.stop()  # Stop the recording immediately and save bytes

            # Process the recorded audio data
            if not audio_bytes:
                logger.warning("recording_stopped | reason=no_audio_found")
                self.orchestrator.handle("bad_audio")
            elif len(audio_bytes) < 1025:
                logger.warning("recording_stopped | reason=audio_too_short")
                self.orchestrator.handle("bad_audio")
            else:
                logger.info(f"recording_stopped | bytes_recorded={len(audio_bytes)}")
                self.handle_audio(audio_bytes)

        """System exit upon escape key press"""
        if key == keyboard.Key.esc:
            sys.exit()

    def handle_audio(self, audio_bytes) -> None:
        """Handle the recorded audio data, e.g., by sending it to the Orchestrator"""
        if audio_bytes is not None:
            self.orchestrator.speak(audio_bytes)

    def listen_for_keypresses(self) -> None:
        """Listen for keypresses to control recording."""
        listener = keyboard.Listener(on_press=self.start_recording, on_release=self.stop_recording)

        listener.start()
        listener.join()
