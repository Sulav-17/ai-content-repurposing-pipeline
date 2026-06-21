import json

import httpx
import pytest

from backend.core.config import Settings
from backend.providers.base import (
    ProviderResponseError,
    ProviderUnavailableError,
)
from backend.providers.ollama import OllamaPlatformContentProvider
from backend.schemas.analysis import KeywordFrequency, TranscriptAnalysis
from backend.schemas.content import ContentBrief
from backend.schemas.generation import PlatformContentAssets


def make_settings() -> Settings:
    return Settings(
        ollama_base_url="http://localhost:11434",
        ollama_model="local-model",
        ollama_timeout_seconds=5,
    )


def make_analysis() -> TranscriptAnalysis:
    return TranscriptAnalysis(
        sentence_count=1,
        unique_word_count=2,
        top_keywords=[KeywordFrequency(term="python", count=1)],
        key_points=["[00:05] Host: Python API wins."],
    )


def make_brief() -> ContentBrief:
    return ContentBrief(
        summary="Python summary.",
        core_message="Python message.",
        target_audience="General audience.",
        key_takeaways=["[00:05] Host: Python API wins."],
        suggested_tone="Clear.",
        source_keywords=["python"],
    )


def valid_assets_payload() -> dict[str, object]:
    return {
        "youtube_titles": [
            "Title 1",
            "Title 2",
            "Title 3",
            "Title 4",
            "Title 5",
        ],
        "youtube_description": "Description.",
        "youtube_chapters": [{"timestamp": "00:05", "title": "Python API wins"}],
        "linkedin_post": "LinkedIn post.",
        "short_hooks": ["Hook 1", "Hook 2", "Hook 3", "Hook 4", "Hook 5"],
        "short_form_concepts": ["Concept 1", "Concept 2", "Concept 3"],
        "portfolio_notes": ["Note 1", "Note 2", "Note 3"],
        "project_summary": "Project summary.",
    }


def call_provider(allowed_timestamps: list[str] | None = None) -> PlatformContentAssets:
    timestamps = ["00:05"] if allowed_timestamps is None else allowed_timestamps
    return OllamaPlatformContentProvider(make_settings()).generate_assets(
        project_name="Demo Project",
        cleaned_text="[00:05] Host: Python API wins.",
        analysis=make_analysis(),
        brief=make_brief(),
        allowed_timestamps=timestamps,
    )


def test_ollama_generation_sends_expected_local_request(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return httpx.Response(
            200,
            json={"response": json_module.dumps(valid_assets_payload())},
        )

    json_module = json
    monkeypatch.setattr(httpx, "post", fake_post)

    result = call_provider()

    assert isinstance(result, PlatformContentAssets)
    assert captured["url"] == "http://localhost:11434/api/generate"
    assert captured["timeout"] == 5
    assert captured["json"]["model"] == "local-model"
    assert captured["json"]["stream"] is False
    assert captured["json"]["format"] == "json"


def test_ollama_generation_prompt_contains_structured_context(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_post(url, json, timeout):
        captured["prompt"] = json["prompt"]
        return httpx.Response(
            200,
            json={"response": json_module.dumps(valid_assets_payload())},
        )

    json_module = json
    monkeypatch.setattr(httpx, "post", fake_post)

    call_provider()

    prompt = captured["prompt"]
    assert "Demo Project" in prompt
    assert "[00:05] Host: Python API wins." in prompt
    assert "\"allowed_timestamps\"" not in prompt
    assert "[\"00:05\"]" in prompt
    assert "Python summary." in prompt


def test_ollama_generation_parses_and_validates_result(monkeypatch) -> None:
    monkeypatch.setattr(
        httpx,
        "post",
        lambda *args, **kwargs: httpx.Response(
            200,
            json={"response": json.dumps(valid_assets_payload())},
        ),
    )

    result = call_provider()

    assert result.youtube_titles == ["Title 1", "Title 2", "Title 3", "Title 4", "Title 5"]


def test_ollama_generation_handles_timeout(monkeypatch) -> None:
    def fake_post(*args, **kwargs):
        raise httpx.TimeoutException("timed out")

    monkeypatch.setattr(httpx, "post", fake_post)

    with pytest.raises(ProviderUnavailableError):
        call_provider()


def test_ollama_generation_handles_connection_failure(monkeypatch) -> None:
    def fake_post(*args, **kwargs):
        raise httpx.ConnectError("connection failed")

    monkeypatch.setattr(httpx, "post", fake_post)

    with pytest.raises(ProviderUnavailableError):
        call_provider()


def test_ollama_generation_handles_invalid_json(monkeypatch) -> None:
    monkeypatch.setattr(
        httpx,
        "post",
        lambda *args, **kwargs: httpx.Response(200, json={"response": "{bad json"}),
    )

    with pytest.raises(ProviderResponseError):
        call_provider()


def test_ollama_generation_handles_invalid_schema(monkeypatch) -> None:
    payload = valid_assets_payload()
    payload["youtube_titles"] = ["Only one title"]
    monkeypatch.setattr(
        httpx,
        "post",
        lambda *args, **kwargs: httpx.Response(
            200,
            json={"response": json.dumps(payload)},
        ),
    )

    with pytest.raises(ProviderResponseError):
        call_provider()


def test_ollama_generation_rejects_fabricated_timestamp(monkeypatch) -> None:
    payload = valid_assets_payload()
    payload["youtube_chapters"] = [{"timestamp": "99:99", "title": "Fabricated"}]
    monkeypatch.setattr(
        httpx,
        "post",
        lambda *args, **kwargs: httpx.Response(
            200,
            json={"response": json.dumps(payload)},
        ),
    )

    with pytest.raises(ProviderResponseError):
        call_provider()


def test_ollama_generation_requires_empty_chapters_when_no_timestamps(monkeypatch) -> None:
    monkeypatch.setattr(
        httpx,
        "post",
        lambda *args, **kwargs: httpx.Response(
            200,
            json={"response": json.dumps(valid_assets_payload())},
        ),
    )

    with pytest.raises(ProviderResponseError):
        call_provider(allowed_timestamps=[])
