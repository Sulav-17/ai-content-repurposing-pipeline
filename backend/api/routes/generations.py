from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from backend.database.session import get_db_session
from backend.providers.base import (
    ProviderConfigurationError,
    ProviderResponseError,
    ProviderUnavailableError,
)
from backend.schemas.generation import ContentGenerationRequest
from backend.schemas.history import GenerationListResponse, SavedGenerationResponse
from backend.services import generation_history_service


router = APIRouter(prefix="/generations", tags=["generations"])


@router.post("", response_model=SavedGenerationResponse, status_code=status.HTTP_201_CREATED)
def create_generation(
    request: ContentGenerationRequest,
    session: Session = Depends(get_db_session),
) -> SavedGenerationResponse:
    try:
        return generation_history_service.create_saved_generation(
            request=request,
            session=session,
        )
    except (ProviderConfigurationError, ProviderUnavailableError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ProviderResponseError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("", response_model=GenerationListResponse)
def list_generations(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_db_session),
) -> GenerationListResponse:
    return generation_history_service.list_generations(
        session=session,
        limit=limit,
        offset=offset,
    )


@router.get("/{generation_id}", response_model=SavedGenerationResponse)
def get_generation(
    generation_id: str,
    session: Session = Depends(get_db_session),
) -> SavedGenerationResponse:
    return generation_history_service.get_saved_generation(
        session=session,
        generation_id=generation_id,
    )


@router.delete("/{generation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_generation(
    generation_id: str,
    session: Session = Depends(get_db_session),
) -> Response:
    generation_history_service.delete_generation(
        session=session,
        generation_id=generation_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
