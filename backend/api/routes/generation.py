from fastapi import APIRouter, HTTPException

from backend.providers.base import (
    ProviderConfigurationError,
    ProviderResponseError,
    ProviderUnavailableError,
)
from backend.schemas.generation import ContentGenerationRequest, ContentGenerationResponse
from backend.services import content_generation_service


router = APIRouter(prefix="/content", tags=["content"])


@router.post("/generate", response_model=ContentGenerationResponse)
def generate_content(request: ContentGenerationRequest) -> ContentGenerationResponse:
    try:
        return content_generation_service.generate_content_assets(
            text=request.text,
            project_name=request.project_name,
            provider_name=request.provider,
        )
    except (ProviderConfigurationError, ProviderUnavailableError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ProviderResponseError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
