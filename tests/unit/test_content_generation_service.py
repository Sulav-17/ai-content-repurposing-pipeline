import pytest

from backend.providers.base import ProviderResponseError
from backend.schemas.analysis import KeywordFrequency, TranscriptAnalysis
from backend.schemas.content import ContentBrief, ContentBriefResponse
from backend.schemas.generation import ContentGenerationRequest, PlatformContentAssets
from backend.schemas.transcript import TranscriptMetadata
from backend.services import content_generation_service


class StubProvider:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def generate_assets(
        self,
        project_name,
        cleaned_text,
        analysis,
        brief,
        allowed_timestamps,
    ):
        self.calls.append(
            {
                "project_name": project_name,
                "cleaned_text": cleaned_text,
                "analysis": analysis,
                "brief": brief,
                "allowed_timestamps": allowed_timestamps,
            }
        )
        return valid_assets()


def valid_brief_response() -> ContentBriefResponse:
    return ContentBriefResponse(
        provider="deterministic",
        cleaned_text="[00:05] Host: Python API wins.",
        metadata=TranscriptMetadata(
            original_character_count=31,
            cleaned_character_count=31,
            word_count=5,
            line_count=1,
            changed=False,
        ),
        analysis=TranscriptAnalysis(
            sentence_count=1,
            unique_word_count=4,
            top_keywords=[
                KeywordFrequency(term="python", count=1),
                KeywordFrequency(term="api", count=1),
            ],
            key_points=["[00:05] Host: Python API wins."],
        ),
        brief=ContentBrief(
            summary="Summary.",
            core_message="Message.",
            target_audience="Audience.",
            key_takeaways=["[00:05] Host: Python API wins."],
            suggested_tone="Clear.",
            source_keywords=["python", "api"],
        ),
    )


def valid_assets() -> PlatformContentAssets:
    return PlatformContentAssets(
        youtube_titles=["Title 1", "Title 2", "Title 3", "Title 4", "Title 5"],
        youtube_description="Description.",
        youtube_chapters=[{"timestamp": "00:05", "title": "Start"}],
        linkedin_post="Post.",
        short_hooks=["Hook 1", "Hook 2", "Hook 3", "Hook 4", "Hook 5"],
        short_form_concepts=["Concept 1", "Concept 2", "Concept 3"],
        portfolio_notes=["Note 1", "Note 2", "Note 3"],
        project_summary="Summary.",
    )


def test_generation_service_reuses_existing_brief_workflow(monkeypatch) -> None:
    called: list[dict[str, object]] = []

    def fake_generate_content_brief(text, provider_name="deterministic", settings=None):
        called.append({"text": text, "provider_name": provider_name})
        return valid_brief_response()

    monkeypatch.setattr(
        content_generation_service,
        "generate_content_brief",
        fake_generate_content_brief,
    )
    provider = StubProvider()

    response = content_generation_service.generate_content_assets(
        text="source text",
        project_name="Demo",
        provider_name="deterministic",
        provider=provider,
    )

    assert called == [{"text": "source text", "provider_name": "deterministic"}]
    assert response.cleaned_text == "[00:05] Host: Python API wins."
    assert provider.calls[0]["allowed_timestamps"] == ["00:05"]


def test_generation_service_default_deterministic_provider_works() -> None:
    response = content_generation_service.generate_content_assets(
        text="Host: Python API wins.",
        project_name="Demo",
    )

    assert response.provider == "deterministic"
    assert len(response.assets.youtube_titles) == 5
    assert response.markdown_export


def test_generation_service_selects_requested_provider(monkeypatch) -> None:
    selected: list[str] = []
    provider = StubProvider()
    monkeypatch.setattr(
        content_generation_service,
        "generate_content_brief",
        lambda *args, **kwargs: valid_brief_response(),
    )

    def fake_get_platform_provider(provider_name, settings=None):
        selected.append(provider_name)
        return provider

    monkeypatch.setattr(
        content_generation_service,
        "get_platform_provider",
        fake_get_platform_provider,
    )

    content_generation_service.generate_content_assets(
        text="source text",
        project_name="Demo",
        provider_name="ollama",
    )

    assert selected == ["ollama"]


def test_generation_service_validates_provider_assets(monkeypatch) -> None:
    class InvalidProvider:
        def generate_assets(self, *args, **kwargs):
            payload = valid_assets().model_dump()
            payload["youtube_titles"] = ["Only one"]
            return payload

    monkeypatch.setattr(
        content_generation_service,
        "generate_content_brief",
        lambda *args, **kwargs: valid_brief_response(),
    )

    with pytest.raises(ProviderResponseError):
        content_generation_service.generate_content_assets(
            text="source text",
            project_name="Demo",
            provider=InvalidProvider(),
        )


def test_generation_service_calls_markdown_service(monkeypatch) -> None:
    monkeypatch.setattr(
        content_generation_service,
        "generate_content_brief",
        lambda *args, **kwargs: valid_brief_response(),
    )
    monkeypatch.setattr(
        content_generation_service,
        "generate_markdown_export",
        lambda project_name, brief, assets: "Generated Markdown",
    )

    response = content_generation_service.generate_content_assets(
        text="source text",
        project_name="Demo",
        provider=StubProvider(),
    )

    assert response.markdown_export == "Generated Markdown"


def test_generation_service_rejects_provider_chapters_without_source_timestamps(monkeypatch) -> None:
    brief_response = valid_brief_response().model_copy(update={"cleaned_text": "Host: No timestamp."})
    monkeypatch.setattr(
        content_generation_service,
        "generate_content_brief",
        lambda *args, **kwargs: brief_response,
    )

    with pytest.raises(ProviderResponseError):
        content_generation_service.generate_content_assets(
            text="source text",
            project_name="Demo",
            provider=StubProvider(),
        )


def test_generation_request_trims_project_name_and_rejects_invalid_provider() -> None:
    request = ContentGenerationRequest(
        text="Host: Python API wins.",
        project_name="  Demo  ",
    )

    assert request.project_name == "Demo"
    with pytest.raises(ValueError):
        ContentGenerationRequest(
            text="Host: Python API wins.",
            project_name="Demo",
            provider="openai",
        )
