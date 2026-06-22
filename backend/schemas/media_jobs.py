from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from backend.schemas.generation import ContentGenerationResponse


MediaJobStatus = Literal["queued", "started", "finished", "failed", "canceled"]
MediaJobStage = Literal[
    "queued",
    "converting",
    "transcribing",
    "generating",
    "saving",
    "complete",
    "failed",
    "canceled",
]


class TranscriptionSegment(BaseModel):
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(ge=0)
    text: str = Field(min_length=1)

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        trimmed_value = " ".join(value.split())
        if not trimmed_value:
            raise ValueError("text must not be blank")
        return trimmed_value

    @model_validator(mode="after")
    def end_must_not_precede_start(self) -> "TranscriptionSegment":
        if self.end_seconds < self.start_seconds:
            raise ValueError("end_seconds must be greater than or equal to start_seconds")
        return self


class TranscriptionResult(BaseModel):
    text: str = Field(min_length=1)
    segments: list[TranscriptionSegment]
    language: str | None = None

    @field_validator("text")
    @classmethod
    def transcript_must_not_be_blank(cls, value: str) -> str:
        stripped_value = value.strip()
        if not stripped_value:
            raise ValueError("text must not be blank")
        return stripped_value

    @field_validator("language")
    @classmethod
    def language_must_be_trimmed(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped_value = value.strip()
        return stripped_value or None


class MediaJobSubmissionResponse(BaseModel):
    job_id: str
    status: MediaJobStatus
    stage: MediaJobStage
    created_at: datetime


class MediaJobStatusResponse(BaseModel):
    job_id: str
    status: MediaJobStatus
    stage: MediaJobStage
    progress: int = Field(ge=0, le=100)
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str | None = None
    transcription: TranscriptionResult | None = None
    generation: ContentGenerationResponse | None = None
    saved_generation_id: str | None = None
