import re

from pydantic import ValidationError

from backend.core.config import Settings, get_settings
from backend.providers.base import ContentPlatformProvider, ProviderResponseError
from backend.providers.deterministic import DeterministicPlatformContentProvider
from backend.providers.ollama import OllamaPlatformContentProvider
from backend.schemas.generation import ContentGenerationResponse, PlatformContentAssets
from backend.services.content_brief_service import generate_content_brief
from backend.services.markdown_export_service import generate_markdown_export


TIMESTAMP_PATTERN = re.compile(r"\[?(\d{1,2}:\d{2}(?::\d{2})?)\]?")


def generate_content_assets(
    text: str,
    project_name: str,
    provider_name: str = "deterministic",
    provider: ContentPlatformProvider | None = None,
    settings: Settings | None = None,
) -> ContentGenerationResponse:
    brief_response = generate_content_brief(
        text=text,
        provider_name=provider_name,
        settings=settings,
    )
    allowed_timestamps = extract_timestamps(brief_response.cleaned_text)
    selected_provider = provider or get_platform_provider(provider_name, settings)
    provider_result = selected_provider.generate_assets(
        project_name=project_name,
        cleaned_text=brief_response.cleaned_text,
        analysis=brief_response.analysis,
        brief=brief_response.brief,
        allowed_timestamps=allowed_timestamps,
    )
    assets = validate_platform_assets(provider_result, allowed_timestamps)
    markdown_export = generate_markdown_export(
        project_name=project_name,
        brief=brief_response.brief,
        assets=assets,
    )

    return ContentGenerationResponse(
        provider=provider_name,
        project_name=project_name,
        cleaned_text=brief_response.cleaned_text,
        metadata=brief_response.metadata,
        analysis=brief_response.analysis,
        brief=brief_response.brief,
        assets=assets,
        markdown_export=markdown_export,
    )


def get_platform_provider(
    provider_name: str,
    settings: Settings | None = None,
) -> ContentPlatformProvider:
    if provider_name == "deterministic":
        return DeterministicPlatformContentProvider()
    if provider_name == "ollama":
        return OllamaPlatformContentProvider(settings or get_settings())
    raise ValueError(f"Unsupported provider: {provider_name}")


def validate_platform_assets(
    provider_result,
    allowed_timestamps: list[str],
) -> PlatformContentAssets:
    if isinstance(provider_result, PlatformContentAssets):
        assets_payload = provider_result.model_dump()
    else:
        assets_payload = provider_result

    try:
        assets = PlatformContentAssets.model_validate(assets_payload)
    except ValidationError as exc:
        raise ProviderResponseError("Provider returned invalid platform content assets.") from exc
    allowed_timestamp_set = set(allowed_timestamps)
    if not allowed_timestamps and assets.youtube_chapters:
        raise ProviderResponseError("Provider returned chapters when no source timestamps were available.")

    for chapter in assets.youtube_chapters:
        if chapter.timestamp not in allowed_timestamp_set:
            raise ProviderResponseError("Provider returned a chapter timestamp not found in the source transcript.")

    return assets


def extract_timestamps(cleaned_text: str) -> list[str]:
    timestamps: list[str] = []
    seen_timestamps: set[str] = set()
    for match in TIMESTAMP_PATTERN.finditer(cleaned_text):
        timestamp = match.group(1)
        if timestamp not in seen_timestamps:
            seen_timestamps.add(timestamp)
            timestamps.append(timestamp)
    return timestamps
