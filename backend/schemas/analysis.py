from pydantic import BaseModel

from backend.schemas.transcript import TranscriptMetadata


class KeywordFrequency(BaseModel):
    term: str
    count: int


class TranscriptAnalysis(BaseModel):
    sentence_count: int
    unique_word_count: int
    top_keywords: list[KeywordFrequency]
    key_points: list[str]


class TranscriptAnalysisResponse(BaseModel):
    cleaned_text: str
    metadata: TranscriptMetadata
    analysis: TranscriptAnalysis
