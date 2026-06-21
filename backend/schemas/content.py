from typing import Literal

from pydantic import BaseModel, Field, field_validator

from backend.schemas.analysis import TranscriptAnalysis
from backend.schemas.transcript import TranscriptCleanRequest, TranscriptMetadata


class ContentBriefRequest(TranscriptCleanRequest):
    provider: Literal["deterministic", "ollama"] = "deterministic"


class ContentBrief(BaseModel):
    summary: str = Field(min_length=1)
    core_message: str = Field(min_length=1)
    target_audience: str = Field(min_length=1)
    key_takeaways: list[str] = Field(min_length=1, max_length=5)
    suggested_tone: str = Field(min_length=1)
    source_keywords: list[str] = Field(max_length=10)

    @field_validator(
        "summary",
        "core_message",
        "target_audience",
        "suggested_tone",
    )
    @classmethod
    def string_must_not_be_blank(cls, value: str) -> str:
        trimmed_value = value.strip()
        if not trimmed_value:
            raise ValueError("field must not be blank")
        return trimmed_value

    @field_validator("key_takeaways", "source_keywords")
    @classmethod
    def list_items_must_not_be_blank(cls, values: list[str]) -> list[str]:
        trimmed_values = [value.strip() for value in values]
        if any(not value for value in trimmed_values):
            raise ValueError("list items must not be blank")
        return trimmed_values


class ContentBriefResponse(BaseModel):
    provider: str
    cleaned_text: str
    metadata: TranscriptMetadata
    analysis: TranscriptAnalysis
    brief: ContentBrief
