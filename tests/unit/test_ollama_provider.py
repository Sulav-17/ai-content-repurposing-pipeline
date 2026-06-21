import json

import httpx
import pytest

from backend.core.config import Settings
from backend.providers.base import (
    ProviderConfigurationError,
    ProviderResponseError,
    ProviderUnavailableError,
)
from backend.providers.ollama import OllamaContentBriefProvider
from backend.schemas.content import ContentBrief


def make_settings() -> Settings:
    return Settings(
        ollama_base_url="http://localhost:11434",
        ollama_model="llama-local",
        ollama_timeout_seconds=3,
    )


def valid_brief_payload() -> dict[str, object]:
    return {
        "summary": "Python API summary.",
        "core_message": "Python API message.",
        "target_audience": "General audience.",
        "key_takeaways": ["Python API wins."],
        "suggested_tone": "Clear.",
        "source_keywords": ["python", "api"],
    }


def test_ollama_provider_sends_expected_local_request(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return httpx.Response(
            200,
            json={"response": json_module.dumps(valid_brief_payload())},
        )

    json_module = json
    monkeypatch.setattr(httpx, "post", fake_post)

    result = OllamaContentBriefProvider(make_settings()).generate_brief(
        cleaned_text="Host: Python API wins.",
        keywords=["python", "api"],
        key_points=["Host: Python API wins."],
    )

    assert isinstance(result, ContentBrief)
    assert captured["url"] == "http://localhost:11434/api/generate"
    assert captured["timeout"] == 3
    assert captured["json"]["model"] == "llama-local"
    assert captured["json"]["stream"] is False
    assert captured["json"]["format"] == "json"
    assert "Host: Python API wins." in captured["json"]["prompt"]


def test_ollama_provider_parses_valid_json_response(monkeypatch) -> None:
    monkeypatch.setattr(
        httpx,
        "post",
        lambda *args, **kwargs: httpx.Response(
            200,
            json={"response": json.dumps(valid_brief_payload())},
        ),
    )

    result = OllamaContentBriefProvider(make_settings()).generate_brief(
        cleaned_text="Host: Python API wins.",
        keywords=["python", "api"],
        key_points=["Host: Python API wins."],
    )

    assert result.summary == "Python API summary."


def test_ollama_provider_validates_content_brief_schema(monkeypatch) -> None:
    payload = valid_brief_payload()
    payload["summary"] = "  Trimmed summary.  "

    monkeypatch.setattr(
        httpx,
        "post",
        lambda *args, **kwargs: httpx.Response(
            200,
            json={"response": json.dumps(payload)},
        ),
    )

    result = OllamaContentBriefProvider(make_settings()).generate_brief(
        cleaned_text="Host: Python API wins.",
        keywords=["python", "api"],
        key_points=["Host: Python API wins."],
    )

    assert result.summary == "Trimmed summary."


def test_ollama_provider_requires_configured_model() -> None:
    settings = Settings(
        ollama_base_url="http://localhost:11434",
        ollama_model="",
        ollama_timeout_seconds=3,
    )

    with pytest.raises(ProviderConfigurationError):
        OllamaContentBriefProvider(settings).generate_brief(
            cleaned_text="Host: Python API wins.",
            keywords=["python"],
            key_points=["Host: Python API wins."],
        )


def test_ollama_provider_handles_unavailable_server(monkeypatch) -> None:
    def fake_post(*args, **kwargs):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(httpx, "post", fake_post)

    with pytest.raises(ProviderUnavailableError):
        OllamaContentBriefProvider(make_settings()).generate_brief(
            cleaned_text="Host: Python API wins.",
            keywords=["python"],
            key_points=["Host: Python API wins."],
        )


def test_ollama_provider_handles_timeout(monkeypatch) -> None:
    def fake_post(*args, **kwargs):
        raise httpx.TimeoutException("timed out")

    monkeypatch.setattr(httpx, "post", fake_post)

    with pytest.raises(ProviderUnavailableError):
        OllamaContentBriefProvider(make_settings()).generate_brief(
            cleaned_text="Host: Python API wins.",
            keywords=["python"],
            key_points=["Host: Python API wins."],
        )


def test_ollama_provider_handles_malformed_payload(monkeypatch) -> None:
    monkeypatch.setattr(
        httpx,
        "post",
        lambda *args, **kwargs: httpx.Response(200, json={"message": "missing response"}),
    )

    with pytest.raises(ProviderResponseError):
        OllamaContentBriefProvider(make_settings()).generate_brief(
            cleaned_text="Host: Python API wins.",
            keywords=["python"],
            key_points=["Host: Python API wins."],
        )


def test_ollama_provider_handles_invalid_generated_json(monkeypatch) -> None:
    monkeypatch.setattr(
        httpx,
        "post",
        lambda *args, **kwargs: httpx.Response(200, json={"response": "{not json"}),
    )

    with pytest.raises(ProviderResponseError):
        OllamaContentBriefProvider(make_settings()).generate_brief(
            cleaned_text="Host: Python API wins.",
            keywords=["python"],
            key_points=["Host: Python API wins."],
        )


def test_ollama_provider_handles_invalid_generated_schema(monkeypatch) -> None:
    payload = valid_brief_payload()
    payload["key_takeaways"] = []

    monkeypatch.setattr(
        httpx,
        "post",
        lambda *args, **kwargs: httpx.Response(
            200,
            json={"response": json.dumps(payload)},
        ),
    )

    with pytest.raises(ProviderResponseError):
        OllamaContentBriefProvider(make_settings()).generate_brief(
            cleaned_text="Host: Python API wins.",
            keywords=["python"],
            key_points=["Host: Python API wins."],
        )
