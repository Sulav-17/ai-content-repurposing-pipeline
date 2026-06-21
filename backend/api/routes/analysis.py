from fastapi import APIRouter

from backend.schemas.analysis import (
    KeywordFrequency,
    TranscriptAnalysis,
    TranscriptAnalysisResponse,
)
from backend.schemas.transcript import TranscriptCleanRequest
from backend.services.content_analysis_service import analyze_transcript


router = APIRouter(prefix="/transcripts", tags=["transcripts"])


@router.post("/analyze", response_model=TranscriptAnalysisResponse)
def analyze_transcript_endpoint(
    request: TranscriptCleanRequest,
) -> TranscriptAnalysisResponse:
    result = analyze_transcript(request.text)

    return TranscriptAnalysisResponse(
        cleaned_text=result.cleaned_text,
        metadata=result.metadata,
        analysis=TranscriptAnalysis(
            sentence_count=result.sentence_count,
            unique_word_count=result.unique_word_count,
            top_keywords=[
                KeywordFrequency(term=keyword.term, count=keyword.count)
                for keyword in result.top_keywords
            ],
            key_points=result.key_points,
        ),
    )
