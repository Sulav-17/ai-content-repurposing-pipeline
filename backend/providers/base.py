from typing import Protocol

from backend.schemas.content import ContentBrief


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
