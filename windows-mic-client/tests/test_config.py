from __future__ import annotations

import sys
from pathlib import Path

CLIENT_SRC = Path(__file__).resolve().parents[1] / "src"
if str(CLIENT_SRC) not in sys.path:
    sys.path.insert(0, str(CLIENT_SRC))

from windows_mic_client.config import load_config


def test_load_config_defaults(monkeypatch):
    monkeypatch.delenv("ASSISTANT_API_BASE_URL", raising=False)
    monkeypatch.delenv("ASSISTANT_API_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("MIC_SAMPLE_RATE", raising=False)
    monkeypatch.delenv("MIC_CHANNELS", raising=False)
    monkeypatch.delenv("MIC_BLOCK_SIZE", raising=False)
    monkeypatch.delenv("PLAYBACK_SAMPLE_RATE", raising=False)

    cfg = load_config()

    assert cfg.assistant_api_base_url == "http://127.0.0.1:8000"
    assert cfg.assistant_api_timeout_seconds == 30.0
    assert cfg.mic_sample_rate == 16000
    assert cfg.mic_channels == 1
    assert cfg.mic_block_size == 1024
    assert cfg.playback_sample_rate == 22050


def test_load_config_from_env(monkeypatch):
    monkeypatch.setenv("ASSISTANT_API_BASE_URL", "http://localhost:9000")
    monkeypatch.setenv("ASSISTANT_API_TIMEOUT_SECONDS", "10")
    monkeypatch.setenv("MIC_SAMPLE_RATE", "44100")
    monkeypatch.setenv("MIC_CHANNELS", "2")
    monkeypatch.setenv("MIC_BLOCK_SIZE", "2048")
    monkeypatch.setenv("PLAYBACK_SAMPLE_RATE", "48000")

    cfg = load_config()

    assert cfg.assistant_api_base_url == "http://localhost:9000"
    assert cfg.assistant_api_timeout_seconds == 10.0
    assert cfg.mic_sample_rate == 44100
    assert cfg.mic_channels == 2
    assert cfg.mic_block_size == 2048
    assert cfg.playback_sample_rate == 48000
