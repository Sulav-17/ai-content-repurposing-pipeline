from pydantic import BaseModel, Field, field_validator


class TranscriptCleanRequest(BaseModel):
    text: str = Field(min_length=1, max_length=200_000)

    @field_validator("text")
    @classmethod
    def text_must_not_be_whitespace_only(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("text must contain at least one non-whitespace character")
        return value


class TranscriptMetadata(BaseModel):
    original_character_count: int
    cleaned_character_count: int
    word_count: int
    line_count: int
    changed: bool


class TranscriptCleanResponse(BaseModel):
    cleaned_text: str
    metadata: TranscriptMetadata
