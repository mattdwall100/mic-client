from __future__ import annotations

import pytest

from windows_mic_client.core.config import ClientSettings, get_client_settings


ENV_KEYS = (
    "ASSISTANT_API_BASE_URL",
    "LIFECYCLE_MANAGER_BASE_URL",
    "ASSISTANT_API_TIMEOUT_SECONDS",
    "MIC_SAMPLE_RATE",
    "MIC_CHANNELS",
    "MIC_BLOCK_SIZE",
    "PLAYBACK_SAMPLE_RATE",
    "LOG_LEVEL",
    "FALLBACK_PATH",
)


@pytest.fixture
def isolated_env(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def test_client_settings_defaults_without_env_file(isolated_env):
    cfg = ClientSettings()

    assert cfg.assistant_api_base_url == "http://localhost:8000"
    assert cfg.lifecycle_manager_base_url == "http://localhost:9000"
    assert cfg.assistant_api_timeout_seconds == 300.0
    assert cfg.mic_sample_rate == 16000
    assert cfg.mic_channels == 1
    assert cfg.mic_block_size == 1024
    assert cfg.playback_sample_rate == 22050
    assert cfg.log_level == "INFO"
    assert cfg.fallback_path == "assets/fallback_audio"


def test_client_settings_reads_environment(monkeypatch, isolated_env):
    monkeypatch.setenv("ASSISTANT_API_BASE_URL", "http://assistant.test:8123/")
    monkeypatch.setenv("LIFECYCLE_MANAGER_BASE_URL", "http://lifecycle.test:9123/")
    monkeypatch.setenv("ASSISTANT_API_TIMEOUT_SECONDS", "12.5")
    monkeypatch.setenv("MIC_SAMPLE_RATE", "44100")
    monkeypatch.setenv("MIC_CHANNELS", "2")
    monkeypatch.setenv("MIC_BLOCK_SIZE", "2048")
    monkeypatch.setenv("PLAYBACK_SAMPLE_RATE", "48000")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("FALLBACK_PATH", "custom/fallbacks")

    cfg = ClientSettings()

    assert cfg.assistant_api_base_url == "http://assistant.test:8123/"
    assert cfg.lifecycle_manager_base_url == "http://lifecycle.test:9123/"
    assert cfg.assistant_api_timeout_seconds == 12.5
    assert cfg.mic_sample_rate == 44100
    assert cfg.mic_channels == 2
    assert cfg.mic_block_size == 2048
    assert cfg.playback_sample_rate == 48000
    assert cfg.log_level == "DEBUG"
    assert cfg.fallback_path == "custom/fallbacks"


def test_get_client_settings_is_cached(monkeypatch, isolated_env):
    monkeypatch.setenv("ASSISTANT_API_BASE_URL", "http://first.test")
    first = get_client_settings()

    monkeypatch.setenv("ASSISTANT_API_BASE_URL", "http://second.test")
    second = get_client_settings()

    assert second is first
    assert second.assistant_api_base_url == "http://first.test"
