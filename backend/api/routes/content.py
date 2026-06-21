from fastapi import APIRouter, HTTPException

from backend.providers.base import (
    ProviderConfigurationError,
    ProviderResponseError,
    ProviderUnavailableError,
)
from backend.schemas.content import ContentBriefRequest, ContentBriefResponse
from backend.services import content_brief_service


router = APIRouter(prefix="/content", tags=["content"])


@router.post("/brief", response_model=ContentBriefResponse)
def create_content_brief(request: ContentBriefRequest) -> ContentBriefResponse:
    try:
        return content_brief_service.generate_content_brief(
            text=request.text,
            provider_name=request.provider,
        )
    except (ProviderConfigurationError, ProviderUnavailableError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ProviderResponseError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
