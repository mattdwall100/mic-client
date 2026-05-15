# Local AI Assistant Mic Clients

Client-side microphone/speaker applications for the Local AI Assistant system. This repository contains the lightweight edge clients that capture audio, send it to the `local-assistant-server`, receive streamed audio responses, and play them locally.

The server performs the AI-heavy work: STT, LLM inference, tool execution, memory, and TTS. The clients stay focused on device I/O, local controls, playback, and local fallback behavior.

## Projects

- `windows-mic-client/`: implemented Windows push-to-talk client for local development and desktop use.
- `raspberry-pi-client/`: planned Raspberry Pi edge client for wake-word, microphone, and speaker deployment.

## What The Windows Client Implements

- Push-to-talk recording using the spacebar.
- Microphone capture with `sounddevice`, NumPy frame handling, and WAV byte conversion.
- Multipart audio upload to the assistant server `/speak` and `/transcribe` endpoints.
- Streaming TTS playback from server responses.
- Interruptible playback so new speech input can stop current audio output.
- Session ID tracking across interactions.
- Server health checks and lifecycle-manager start/stop hooks.
- Client-side fallback audio for bad recordings or unavailable server.
- Environment-backed configuration for API URLs, timeouts, mic settings, playback settings, and fallback paths.
- Unit and integration-style tests using fakes/monkeypatching around hardware and network boundaries.

## Technologies

- Python 3.11-3.13
- sounddevice, soundfile, NumPy
- pynput
- requests
- Pydantic v2, pydantic-settings
- pytest, pytest-cov
- Ruff, mypy
- Docker/Docker Compose assets

## Engineering Practices Demonstrated

- Clear edge/server separation: the client handles I/O; the server handles inference.
- Modular client architecture: audio recorder, audio player, API client, orchestrator, fallback handler, config, logging.
- Testable hardware boundaries using fakes and monkeypatching instead of requiring a real microphone/server during tests.
- Latency logging around API calls and user interactions.
- Configurable runtime behavior through `.env` and typed settings.
- Graceful degradation through local fallback WAV files.
- Roadmap-aware design for moving from Windows development to Raspberry Pi deployment.

## Repository Structure

```text
mic-client/
|-- README.md
|-- requirements.txt
|-- external/
|-- raspberry-pi-client/
|   `-- README.md                     # Planned Raspberry Pi client
`-- windows-mic-client/
    |-- README.md
    |-- src/
    |   `-- windows_mic_client/
    |       |-- main.py               # Client composition and startup flow
    |       |-- audio/
    |       |   |-- recorder.py       # Push-to-talk recording
    |       |   |-- player.py         # WAV/stream playback
    |       |   `-- audio_utils.py    # WAV byte conversion
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
    |   |-- test_assistant_api_client.py
    |   |-- test_audio_utils.py
    |   |-- test_config.py
    |   |-- test_fallback.py
    |   |-- test_integration_flows.py
    |   |-- test_orchestrator.py
    |   |-- test_player.py
    |   `-- test_recorder_controller.py
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

## Running The Windows Client

Start the assistant server first, then run:

```powershell
cd windows-mic-client
.\scripts\run_client.ps1
```

Hold `Space` to record. Release `Space` to send the WAV audio to the server. Press `Esc` to request server shutdown through the lifecycle manager and exit.

## Testing

```powershell
cd windows-mic-client
.\.venv\Scripts\python.exe -m pytest
```

The Windows client test suite validates API calls, orchestration, fallback behavior, config loading, WAV conversion, playback streaming, and push-to-talk control flow.
