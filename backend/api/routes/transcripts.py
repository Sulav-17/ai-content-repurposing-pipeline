from fastapi import APIRouter

from backend.schemas.transcript import TranscriptCleanRequest, TranscriptCleanResponse
from backend.services.transcript_service import clean_transcript


router = APIRouter(prefix="/transcripts", tags=["transcripts"])


@router.post("/clean", response_model=TranscriptCleanResponse)
def clean_transcript_endpoint(request: TranscriptCleanRequest) -> TranscriptCleanResponse:
    result = clean_transcript(request.text)

    return TranscriptCleanResponse(
        cleaned_text=result.cleaned_text,
        metadata=result.metadata,
    )
