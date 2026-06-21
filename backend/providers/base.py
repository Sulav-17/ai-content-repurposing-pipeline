from typing import Protocol

from backend.schemas.analysis import TranscriptAnalysis
from backend.schemas.content import ContentBrief
from backend.schemas.generation import PlatformContentAssets


class ProviderConfigurationError(Exception):
    pass


class ProviderUnavailableError(Exception):
    pass


class ProviderResponseError(Exception):
    pass


class ContentBriefProvider(Protocol):
    def generate_brief(
        self,
        cleaned_text: str,
        keywords: list[str],
        key_points: list[str],
    ) -> ContentBrief:
        ...


class ContentPlatformProvider(Protocol):
    def generate_assets(
        self,
        project_name: str,
        cleaned_text: str,
        analysis: TranscriptAnalysis,
        brief: ContentBrief,
        allowed_timestamps: list[str],
    ) -> PlatformContentAssets:
        ...
