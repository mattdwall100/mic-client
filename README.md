- `windows-mic-client/`: first client for use with local server, for speaking to the local AI assistant program.
- `raspberry-pi-client/`: target edge client with wake-word, mic, and speaker.

mic-client/
├─ README.md
├─ requirements.txt
├─ external/
├─ raspberry-pi-client/
│ └─ README.md
└─ windows-mic-client/
├─ README.md
├─ requirements.txt
├─ requirements-dev.txt
├─ Dockerfile
├─ docker-compose.yml
├─ assets/
│ └─ fallback_audio/
├─ scripts/
│ └─ run_client.ps1
├─ tests/
│ ├─ test_config.py
│ └─ audio_files/
└─ src/
└─ windows_mic_client/
├─ **init**.py
├─ main.py
├─ audio/
│ ├─ recorder.py
│ ├─ player.py
│ └─ audio_utils.py
├─ client/
│ ├─ **init**.py
│ └─ assistant_api_client.py
├─ core/
│ ├─ config.py
│ └─ logging.py
├─ orchestrator/
│ ├─ **init**.py
│ ├─ orchestrator.py
│ └─ fallback.py
└─ utils/
└─ latency_logger.py
