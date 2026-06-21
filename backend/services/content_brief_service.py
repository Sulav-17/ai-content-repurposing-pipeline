from backend.core.config import Settings, get_settings
from backend.providers.base import ContentBriefProvider
from backend.providers.deterministic import DeterministicContentBriefProvider
from backend.providers.ollama import OllamaContentBriefProvider
from backend.schemas.analysis import KeywordFrequency, TranscriptAnalysis
from backend.schemas.content import ContentBrief, ContentBriefResponse
from backend.services.content_analysis_service import analyze_transcript


def generate_content_brief(
    text: str,
    provider_name: str = "deterministic",
    provider: ContentBriefProvider | None = None,
    settings: Settings | None = None,
) -> ContentBriefResponse:
    analysis_result = analyze_transcript(text)
    analysis = TranscriptAnalysis(
        sentence_count=analysis_result.sentence_count,
        unique_word_count=analysis_result.unique_word_count,
        top_keywords=[
            KeywordFrequency(term=keyword.term, count=keyword.count)
            for keyword in analysis_result.top_keywords
        ],
        key_points=analysis_result.key_points,
    )
    keywords = [keyword.term for keyword in analysis_result.top_keywords]
    selected_provider = provider or get_provider(provider_name, settings)
    brief = ContentBrief.model_validate(
        selected_provider.generate_brief(
            cleaned_text=analysis_result.cleaned_text,
            keywords=keywords,
            key_points=analysis_result.key_points,
        )
    )

    return ContentBriefResponse(
        provider=provider_name,
        cleaned_text=analysis_result.cleaned_text,
        metadata=analysis_result.metadata,
        analysis=analysis,
        brief=brief,
    )


def get_provider(
    provider_name: str,
    settings: Settings | None = None,
) -> ContentBriefProvider:
    if provider_name == "deterministic":
        return DeterministicContentBriefProvider()
    if provider_name == "ollama":
        return OllamaContentBriefProvider(settings or get_settings())
    raise ValueError(f"Unsupported provider: {provider_name}")
