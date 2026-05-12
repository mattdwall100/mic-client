from __future__ import annotations

from pydantic import BaseModel
from types import SimpleNamespace
import requests

import pytest

from windows_mic_client.client import assistant_api_client as api_module
from windows_mic_client.client.assistant_api_client import AssistantAPIClient


class HealthResponse(BaseModel):
    status: str = "ok"
    status_code: int = 200


class ChatResponse(BaseModel):
    text: str
    session_id: str | None = None


def make_response_from_model(model, status_code: int = 200) -> requests.Response:
    response = requests.Response()
    response.status_code = status_code
    response._content = model.model_dump_json().encode("utf-8")
    response.headers["Content-Type"] = "application/json"
    return response


# In the future just use testclient for all fast api tests
def make_response_from_chunks(chunks=[b"chunk-1", b"chunk-2"]):
    response = requests.Response()
    response.status_code = 200
    response.headers["Content-Type"] = "application/octet-stream"
    response.headers["X-Session-ID"] = "session-stream"

    response._content = b"".join(
        chunk if isinstance(chunk, bytes) else chunk.encode("utf-8") for chunk in chunks
    )

    return response


@pytest.fixture
def api_settings(monkeypatch):
    settings = SimpleNamespace(
        assistant_api_base_url="http://assistant.test/api/",
        lifecycle_manager_base_url="http://lifecycle.test/api/",
        assistant_api_timeout_seconds=42.0,
    )
    monkeypatch.setattr(api_module, "settings", settings)
    return settings


def test_client_uses_loaded_settings_for_urls_and_timeout(api_settings):
    client = AssistantAPIClient(base_url="http://ignored.test", timeout_seconds=1.0)

    assert client.base_url == "http://assistant.test/api"
    assert client.lifecycle_manager_base_url == "http://lifecycle.test/api"
    assert client.timeout_seconds == 42.0


@pytest.mark.parametrize(
    ("payload", "expected"),
    [("ok", True), ("down", False)],
)
def test_health_returns_status_from_json(monkeypatch, api_settings, payload, expected):
    def fake_get(url, timeout):
        assert url == "http://assistant.test/api/health"
        assert timeout == 42.0
        return make_response_from_model(HealthResponse(status=payload))

    monkeypatch.setattr(api_module.requests, "get", fake_get)

    assert AssistantAPIClient("ignored").health() is expected


def test_health_returns_false_on_request_error(monkeypatch, api_settings):
    def fake_get(url, timeout):
        raise TimeoutError("no server")

    monkeypatch.setattr(api_module.requests, "get", fake_get)

    assert AssistantAPIClient("ignored").health() is False


def test_speak_posts_audio_and_returns_response_with_session(monkeypatch, api_settings):
    # response = SimpleNamespace(headers={"X-Session-ID": "session-2", "X-Fallback-TXT": "unused"})
    # response= # Send back the stream response
    response = make_response_from_chunks()

    captured = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return response

    monkeypatch.setattr(api_module.requests, "post", fake_post)

    result, session_id = AssistantAPIClient("ignored").speak(b"wav", "session-stream")

    assert result is response
    assert session_id == "session-stream"
    assert captured["url"] == "http://assistant.test/api/speak"
    assert captured["files"] == {"file": ("audio.wav", b"wav", "audio/wav")}
    assert captured["data"] == {"session_id": "session-stream"}
    assert captured["timeout"] == 42.0


def test_synthesize_posts_text_payload_as_stream(monkeypatch, api_settings):
    response = make_response_from_chunks()

    captured = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return response

    monkeypatch.setattr(api_module.requests, "post", fake_post)

    result, session_id = AssistantAPIClient("ignored").synthesize("hello", None)

    assert result is response
    assert session_id == "session-stream"
    assert captured == {
        "url": "http://assistant.test/api/synthesize",
        "json": {"text": "hello", "session_id": None},
        "timeout": 42.0,
        "stream": True,
    }


def test_transcribe_posts_audio_and_returns_json(monkeypatch, api_settings):
    response = make_response_from_model(ChatResponse(text="hello"))

    captured = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return response

    monkeypatch.setattr(api_module.requests, "post", fake_post)

    result = AssistantAPIClient("ignored").transcribe(b"wav", "session-1")

    assert result["text"] == "hello"
    assert captured["url"] == "http://assistant.test/api/transcribe"
    assert captured["files"] == {"file": ("audio.wav", b"wav", "audio/wav")}
    assert captured["data"] == {"session_id": "session-1"}
    assert captured["timeout"] == 42.0


def test_lifecycle_methods_post_to_lifecycle_manager(monkeypatch, api_settings):
    posted_urls = []
    monkeypatch.setattr(
        api_module.requests, "post", lambda url, **kwargs: posted_urls.append(url)
    )
    client = AssistantAPIClient("ignored")

    client.wake_server()
    client.close_server()

    assert posted_urls == [
        "http://lifecycle.test/api/services/local-assistant-server/start",
        "http://lifecycle.test/api/services/local-assistant-server/stop",
    ]
