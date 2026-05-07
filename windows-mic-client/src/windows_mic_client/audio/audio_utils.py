import io

import soundfile as sf


def numpy_to_wav_bytes(np_audio, sample_rate):
    memory_buffer = io.BytesIO()
    sf.write(memory_buffer, np_audio, sample_rate, format="WAV")
    memory_buffer.seek(0)
    return memory_buffer.read()
