from __future__ import annotations

import io

import numpy as np
import soundfile as sf

from windows_mic_client.audio.audio_utils import numpy_to_wav_bytes


def test_numpy_to_wav_bytes_returns_readable_wav():
    sample_rate = 16_000
    audio = np.array([[0], [1000], [-1000], [500]], dtype=np.int16)

    wav_bytes = numpy_to_wav_bytes(audio, sample_rate)
    decoded_audio, decoded_sample_rate = sf.read(io.BytesIO(wav_bytes), dtype="int16")

    assert wav_bytes.startswith(b"RIFF")
    assert decoded_sample_rate == sample_rate
    assert decoded_audio.tolist() == [0, 1000, -1000, 500]
