from pathlib import Path
from typing import Any

from backend.database.session import get_sessionmaker
from backend.providers.base import ProviderConfigurationError, ProviderResponseError, ProviderUnavailableError
from backend.schemas.generation import ContentGenerationRequest, ContentGenerationResponse
from backend.schemas.media_jobs import TranscriptionResult
from backend.services.content_generation_service import generate_content_assets
from backend.services.generation_history_service import persist_generated_response
from backend.services.media_conversion_service import (
    MediaConversionConfigurationError,
    MediaConversionError,
    convert_to_wav,
)
from backend.services.media_job_service import mark_job_stage
from backend.transcription.base import TranscriptionConfigurationError, TranscriptionError
from backend.transcription.whisper_cpp import WhisperCppTranscriber


def process_media_job(
    upload_path: str,
    project_name: str,
    provider: str,
    save_result: bool,
    language: str | None = None,
) -> dict[str, Any]:
    job = get_current_job()
    wav_path: Path | None = None
    upload = Path(upload_path)

    try:
        if job is not None:
            mark_job_stage(job, "started", "converting")
        wav_path = convert_to_wav(upload)

        if job is not None:
            mark_job_stage(job, "started", "transcribing")
        transcription = WhisperCppTranscriber().transcribe(wav_path, language=language)

        if job is not None:
            mark_job_stage(job, "started", "generating")
        request = ContentGenerationRequest(
            text=transcription.text,
            project_name=project_name,
            provider=provider,
        )
        generation = generate_content_assets(
            text=request.text,
            project_name=request.project_name,
            provider_name=request.provider,
        )

        saved_generation_id = None
        if save_result:
            if job is not None:
                mark_job_stage(job, "started", "saving")
            session = get_sessionmaker()()
            try:
                saved = persist_generated_response(
                    session=session,
                    request=request,
                    generation_response=generation,
                )
                saved_generation_id = saved.id
            finally:
                session.close()

        result = _success_result(transcription, generation, saved_generation_id)
        if job is not None:
            mark_job_stage(job, "finished", "complete", result)
        return result
    except (
        MediaConversionConfigurationError,
        MediaConversionError,
        TranscriptionConfigurationError,
        TranscriptionError,
        ProviderConfigurationError,
        ProviderUnavailableError,
        ProviderResponseError,
        Exception,
    ):
        result = _failure_result()
        if job is not None:
            mark_job_stage(job, "failed", "failed", result)
        return result
    finally:
        _delete_if_exists(upload)
        if wav_path is not None:
            _delete_if_exists(wav_path)


def _success_result(
    transcription: TranscriptionResult,
    generation: ContentGenerationResponse,
    saved_generation_id: str | None,
) -> dict[str, Any]:
    return {
        "status": "finished",
        "stage": "complete",
        "progress": 100,
        "error": None,
        "transcription": transcription.model_dump(mode="json"),
        "generation": generation.model_dump(mode="json"),
        "saved_generation_id": saved_generation_id,
    }


def _failure_result() -> dict[str, Any]:
    return {
        "status": "failed",
        "stage": "failed",
        "progress": 100,
        "error": "Media processing failed.",
        "transcription": None,
        "generation": None,
        "saved_generation_id": None,
    }


def _delete_if_exists(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def get_current_job():
    try:
        from rq import get_current_job as rq_get_current_job
    except ImportError:
        return None
    return rq_get_current_job()
