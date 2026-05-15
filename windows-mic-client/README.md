# Windows Mic Client

Windows push-to-talk microphone client for the Local AI Assistant system. It records audio locally, sends WAV bytes to the `local-assistant-server`, receives a streamed TTS response, and plays the response through the local speaker.

The client is deliberately lightweight: it owns microphone input, keyboard controls, playback, local fallback audio, and API calls. The server owns STT, LLM inference, tool execution, memory, and TTS generation.

## Features

- Spacebar push-to-talk recording with `pynput`.
- Microphone capture using `sounddevice`.
- NumPy/soundfile conversion from recorded frames to WAV bytes.
- HTTP client for `/health`, `/speak`, `/transcribe`, and `/synthesize`.
- Streaming playback of server-generated audio.
- Interruptible playback when the user starts a new recording.
- Session ID tracking across turns.
- Server wake/stop hooks via a lifecycle-manager API.
- Local fallback WAV files for server unavailable or invalid audio.
- Typed environment configuration using Pydantic settings.
- Tests around hardware and network boundaries using fakes and monkeypatching.

## Technologies

- Python 3.11-3.13
- sounddevice, soundfile, NumPy
- pynput
- requests
- Pydantic v2, pydantic-settings
- pytest, pytest-cov
- Ruff, mypy

## Repository Structure

```text
windows-mic-client/
|-- src/
|   `-- windows_mic_client/
|       |-- main.py
|       |-- audio/
|       |   |-- recorder.py
|       |   |-- player.py
|       |   `-- audio_utils.py
|       |-- client/
|       |   `-- assistant_api_client.py
|       |-- core/
|       |   |-- config.py
|       |   `-- logging.py
|       |-- orchestrator/
|       |   |-- orchestrator.py
|       |   `-- fallback.py
|       `-- utils/
|           `-- latency_logger.py
|-- tests/
|-- assets/
|   `-- fallback_audio/
|-- scripts/
|   `-- run_client.ps1
|-- Dockerfile
|-- docker-compose.yml
|-- requirements.txt
|-- requirements-dev.txt
`-- .env.example
```

## Run

```powershell
.\scripts\run_client.ps1
```

Hold `Space` to record and release it to send audio to the server. Press `Esc` to close the server through the lifecycle manager and exit the client.

## Test

```powershell
.\.venv\Scripts\python.exe -m pytest
```
