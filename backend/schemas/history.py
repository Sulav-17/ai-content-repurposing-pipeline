from datetime import datetime

from pydantic import BaseModel

from backend.schemas.generation import ContentGenerationResponse


class GenerationHistoryItem(BaseModel):
    id: str
    project_name: str
    provider: str
    project_summary: str
    created_at: datetime


class GenerationListResponse(BaseModel):
    items: list[GenerationHistoryItem]
    total: int
    limit: int
    offset: int


class SavedGenerationResponse(BaseModel):
    id: str
    created_at: datetime
    generation: ContentGenerationResponse
