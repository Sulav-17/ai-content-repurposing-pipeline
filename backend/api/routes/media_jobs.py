from typing import Literal

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response

from backend.queueing.connection import QueueConfigurationError, QueueUnavailableError
from backend.schemas.media_jobs import MediaJobStatusResponse, MediaJobSubmissionResponse
from backend.services import media_job_service
from backend.services.media_job_service import MediaJobConflictError, MediaJobNotFoundError
from backend.services.media_upload_service import UploadTooLargeError, UploadValidationError, save_upload


router = APIRouter(prefix="/media-jobs", tags=["media-jobs"])


@router.post("", response_model=MediaJobSubmissionResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_media_job(
    file: UploadFile = File(...),
    project_name: str = Form(..., min_length=1, max_length=120),
    provider: Literal["deterministic", "ollama"] = Form("deterministic"),
    save_result: bool = Form(True),
    language: str | None = Form(None),
) -> MediaJobSubmissionResponse:
    trimmed_project_name = project_name.strip()
    if not trimmed_project_name:
        raise HTTPException(status_code=422, detail="project_name must not be blank")
    trimmed_language = language.strip() if isinstance(language, str) and language.strip() else None

    try:
        upload_path = await save_upload(file)
        return media_job_service.submit_media_job(
            upload_path=upload_path,
            project_name=trimmed_project_name,
            provider=provider,
            save_result=save_result,
            language=trimmed_language,
        )
    except UploadTooLargeError as exc:
        raise HTTPException(status_code=413, detail="Uploaded file is too large.") from exc
    except UploadValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (QueueConfigurationError, QueueUnavailableError) as exc:
        raise HTTPException(status_code=503, detail="Media queue is unavailable.") from exc


@router.get("/{job_id}", response_model=MediaJobStatusResponse)
def get_media_job(job_id: str) -> MediaJobStatusResponse:
    try:
        return media_job_service.get_media_job_status(job_id)
    except MediaJobNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Media job was not found.") from exc
    except (QueueConfigurationError, QueueUnavailableError) as exc:
        raise HTTPException(status_code=503, detail="Media queue is unavailable.") from exc


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_media_job(job_id: str) -> Response:
    try:
        media_job_service.cancel_media_job(job_id)
    except MediaJobNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Media job was not found.") from exc
    except MediaJobConflictError as exc:
        raise HTTPException(status_code=409, detail="Media job cannot be canceled.") from exc
    except (QueueConfigurationError, QueueUnavailableError) as exc:
        raise HTTPException(status_code=503, detail="Media queue is unavailable.") from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
