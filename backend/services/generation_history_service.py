from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.database.session import DatabaseUnavailableError
from backend.models.generation import Generation
from backend.repositories.generation_repository import GenerationRepository
from backend.schemas.analysis import TranscriptAnalysis
from backend.schemas.content import ContentBrief
from backend.schemas.generation import ContentGenerationRequest, ContentGenerationResponse, PlatformContentAssets
from backend.schemas.history import GenerationHistoryItem, GenerationListResponse, SavedGenerationResponse
from backend.schemas.transcript import TranscriptMetadata
from backend.services.content_generation_service import generate_content_assets


class GenerationNotFoundError(Exception):
    pass


def create_saved_generation(
    request: ContentGenerationRequest,
    session: Session,
) -> SavedGenerationResponse:
    generation_response = generate_content_assets(
        text=request.text,
        project_name=request.project_name,
        provider_name=request.provider,
    )
    record = Generation(
        id=str(uuid4()),
        project_name=request.project_name,
        provider=request.provider,
        input_text=request.text,
        cleaned_text=generation_response.cleaned_text,
        metadata_json=generation_response.metadata.model_dump(mode="json"),
        analysis_json=generation_response.analysis.model_dump(mode="json"),
        brief_json=generation_response.brief.model_dump(mode="json"),
        assets_json=generation_response.assets.model_dump(mode="json"),
        markdown_export=generation_response.markdown_export,
        created_at=datetime.now(UTC),
    )
    repository = GenerationRepository(session)

    try:
        repository.create(record)
        session.commit()
        session.refresh(record)
    except SQLAlchemyError as exc:
        session.rollback()
        raise DatabaseUnavailableError("Database is unavailable.") from exc

    return _saved_response_from_record(record)


def list_generations(
    session: Session,
    limit: int,
    offset: int,
) -> GenerationListResponse:
    repository = GenerationRepository(session)
    try:
        records = repository.list(limit=limit, offset=offset)
        total = repository.count()
    except SQLAlchemyError as exc:
        raise DatabaseUnavailableError("Database is unavailable.") from exc

    return GenerationListResponse(
        items=[_history_item_from_record(record) for record in records],
        total=total,
        limit=limit,
        offset=offset,
    )


def get_saved_generation(
    session: Session,
    generation_id: str,
) -> SavedGenerationResponse:
    repository = GenerationRepository(session)
    try:
        record = repository.get_by_id(generation_id)
    except SQLAlchemyError as exc:
        raise DatabaseUnavailableError("Database is unavailable.") from exc

    if record is None:
        raise GenerationNotFoundError("Generation was not found.")

    return _saved_response_from_record(record)


def delete_generation(
    session: Session,
    generation_id: str,
) -> None:
    repository = GenerationRepository(session)
    try:
        record = repository.get_by_id(generation_id)
        if record is None:
            raise GenerationNotFoundError("Generation was not found.")
        repository.delete(record)
        session.commit()
    except GenerationNotFoundError:
        session.rollback()
        raise
    except SQLAlchemyError as exc:
        session.rollback()
        raise DatabaseUnavailableError("Database is unavailable.") from exc


def _saved_response_from_record(record: Generation) -> SavedGenerationResponse:
    return SavedGenerationResponse(
        id=record.id,
        created_at=_ensure_utc(record.created_at),
        generation=_generation_response_from_record(record),
    )


def _history_item_from_record(record: Generation) -> GenerationHistoryItem:
    assets = PlatformContentAssets.model_validate(record.assets_json)
    return GenerationHistoryItem(
        id=record.id,
        project_name=record.project_name,
        provider=record.provider,
        project_summary=assets.project_summary,
        created_at=_ensure_utc(record.created_at),
    )


def _generation_response_from_record(record: Generation) -> ContentGenerationResponse:
    return ContentGenerationResponse(
        provider=record.provider,
        project_name=record.project_name,
        cleaned_text=record.cleaned_text,
        metadata=TranscriptMetadata.model_validate(record.metadata_json),
        analysis=TranscriptAnalysis.model_validate(record.analysis_json),
        brief=ContentBrief.model_validate(record.brief_json),
        assets=PlatformContentAssets.model_validate(record.assets_json),
        markdown_export=record.markdown_export,
    )


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
