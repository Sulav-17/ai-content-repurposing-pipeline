import pytest

from backend.schemas.content import ContentBrief, ContentBriefRequest
from backend.schemas.transcript import TranscriptMetadata
from backend.services import content_brief_service
from backend.services.content_analysis_service import (
    KeywordFrequencyResult,
    TranscriptAnalysisResult,
)


class StubProvider:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def generate_brief(self, cleaned_text, keywords, key_points):
        self.calls.append(
            {
                "cleaned_text": cleaned_text,
                "keywords": keywords,
                "key_points": key_points,
            }
        )
        return ContentBrief(
            summary="Stub summary.",
            core_message="Stub message.",
            target_audience="Stub audience.",
            key_takeaways=["Stub takeaway."],
            suggested_tone="Stub tone.",
            source_keywords=keywords,
        )


def fake_analysis_result() -> TranscriptAnalysisResult:
    return TranscriptAnalysisResult(
        cleaned_text="Host: Python API wins.",
        metadata=TranscriptMetadata(
            original_character_count=27,
            cleaned_character_count=22,
            word_count=4,
            line_count=1,
            changed=True,
        ),
        sentence_count=1,
        unique_word_count=4,
        top_keywords=[
            KeywordFrequencyResult(term="api", count=1),
            KeywordFrequencyResult(term="python", count=1),
        ],
        key_points=["Host: Python API wins."],
    )


def test_content_brief_service_reuses_existing_analysis_service(monkeypatch) -> None:
    called_with: list[str] = []

    def fake_analyze_transcript(text: str) -> TranscriptAnalysisResult:
        called_with.append(text)
        return fake_analysis_result()

    monkeypatch.setattr(
        content_brief_service,
        "analyze_transcript",
        fake_analyze_transcript,
    )
    provider = StubProvider()

    response = content_brief_service.generate_content_brief(
        text="  Host:\tPython API wins.  ",
        provider_name="deterministic",
        provider=provider,
    )

    assert called_with == ["  Host:\tPython API wins.  "]
    assert response.cleaned_text == "Host: Python API wins."
    assert provider.calls[0]["cleaned_text"] == "Host: Python API wins."


def test_content_brief_service_selects_requested_provider(monkeypatch) -> None:
    selected: list[str] = []
    provider = StubProvider()

    monkeypatch.setattr(
        content_brief_service,
        "analyze_transcript",
        lambda text: fake_analysis_result(),
    )

    def fake_get_provider(provider_name, settings=None):
        selected.append(provider_name)
        return provider

    monkeypatch.setattr(content_brief_service, "get_provider", fake_get_provider)

    content_brief_service.generate_content_brief(
        text="Host: Python API wins.",
        provider_name="ollama",
    )

    assert selected == ["ollama"]


def test_content_brief_service_deterministic_provider_works() -> None:
    response = content_brief_service.generate_content_brief(
        text="Host: Python API wins.",
        provider_name="deterministic",
    )

    assert response.provider == "deterministic"
    assert response.brief.key_takeaways == ["Host: Python API wins."]
    assert response.analysis.key_points == ["Host: Python API wins."]


def test_content_brief_service_accepts_injected_ollama_provider(monkeypatch) -> None:
    monkeypatch.setattr(
        content_brief_service,
        "analyze_transcript",
        lambda text: fake_analysis_result(),
    )
    provider = StubProvider()

    response = content_brief_service.generate_content_brief(
        text="Host: Python API wins.",
        provider_name="ollama",
        provider=provider,
    )

    assert response.provider == "ollama"
    assert response.brief.summary == "Stub summary."


def test_invalid_provider_values_cannot_pass_request_validation() -> None:
    with pytest.raises(ValueError):
        ContentBriefRequest(text="Host: Python API wins.", provider="openai")
