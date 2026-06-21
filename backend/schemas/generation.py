from typing import Literal

from pydantic import BaseModel, Field, field_validator

from backend.schemas.analysis import TranscriptAnalysis
from backend.schemas.content import ContentBrief
from backend.schemas.transcript import TranscriptCleanRequest, TranscriptMetadata


class ContentGenerationRequest(TranscriptCleanRequest):
    project_name: str = Field(min_length=1, max_length=120)
    provider: Literal["deterministic", "ollama"] = "deterministic"

    @field_validator("project_name", mode="before")
    @classmethod
    def project_name_must_not_be_blank(cls, value) -> str:
        if not isinstance(value, str):
            return value
        trimmed_value = value.strip()
        if not trimmed_value:
            raise ValueError("project_name must not be blank")
        return trimmed_value


class YouTubeChapter(BaseModel):
    timestamp: str = Field(min_length=1)
    title: str = Field(min_length=1)

    @field_validator("timestamp")
    @classmethod
    def timestamp_must_not_be_blank(cls, value: str) -> str:
        normalized_value = value.strip().strip("[]")
        if not normalized_value:
            raise ValueError("timestamp must not be blank")
        return normalized_value

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        trimmed_value = value.strip()
        if not trimmed_value:
            raise ValueError("title must not be blank")
        return trimmed_value


class PlatformContentAssets(BaseModel):
    youtube_titles: list[str] = Field(min_length=5, max_length=5)
    youtube_description: str = Field(min_length=1)
    youtube_chapters: list[YouTubeChapter] = Field(max_length=12)
    linkedin_post: str = Field(min_length=1)
    short_hooks: list[str] = Field(min_length=5, max_length=5)
    short_form_concepts: list[str] = Field(min_length=3, max_length=5)
    portfolio_notes: list[str] = Field(min_length=3, max_length=8)
    project_summary: str = Field(min_length=1)

    @field_validator("youtube_titles", "short_hooks")
    @classmethod
    def values_must_be_nonblank_and_unique(cls, values: list[str]) -> list[str]:
        trimmed_values = [value.strip() for value in values]
        if any(not value for value in trimmed_values):
            raise ValueError("list items must not be blank")

        seen_values: set[str] = set()
        for value in trimmed_values:
            normalized_value = value.casefold()
            if normalized_value in seen_values:
                raise ValueError("list items must be unique")
            seen_values.add(normalized_value)

        return trimmed_values

    @field_validator("short_form_concepts", "portfolio_notes")
    @classmethod
    def values_must_be_nonblank(cls, values: list[str]) -> list[str]:
        trimmed_values = [value.strip() for value in values]
        if any(not value for value in trimmed_values):
            raise ValueError("list items must not be blank")
        return trimmed_values

    @field_validator(
        "youtube_description",
        "linkedin_post",
        "project_summary",
    )
    @classmethod
    def string_must_not_be_blank(cls, value: str) -> str:
        trimmed_value = value.strip()
        if not trimmed_value:
            raise ValueError("field must not be blank")
        return trimmed_value

    @field_validator("youtube_chapters", mode="before")
    @classmethod
    def deduplicate_chapters_by_timestamp(cls, values):
        if values is None:
            return []

        deduplicated_chapters = []
        seen_timestamps: set[str] = set()
        for value in values:
            if isinstance(value, YouTubeChapter):
                chapter_data = value.model_dump()
            else:
                chapter_data = dict(value)

            timestamp = str(chapter_data.get("timestamp", "")).strip().strip("[]")
            if timestamp in seen_timestamps:
                continue
            seen_timestamps.add(timestamp)
            chapter_data["timestamp"] = timestamp
            deduplicated_chapters.append(chapter_data)

        return deduplicated_chapters


class ContentGenerationResponse(BaseModel):
    provider: str
    project_name: str
    cleaned_text: str
    metadata: TranscriptMetadata
    analysis: TranscriptAnalysis
    brief: ContentBrief
    assets: PlatformContentAssets
    markdown_export: str = Field(min_length=1)

    @field_validator("project_name", "markdown_export")
    @classmethod
    def response_string_must_not_be_blank(cls, value: str) -> str:
        trimmed_value = value.strip()
        if not trimmed_value:
            raise ValueError("field must not be blank")
        return trimmed_value
