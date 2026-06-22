from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from backend.core.config import MediaSettings, get_media_settings
from backend.queueing.connection import (
    QueueConfigurationError,
    QueueUnavailableError,
    get_media_queue,
    get_redis_connection,
)
from backend.schemas.media_jobs import MediaJobStatusResponse, MediaJobSubmissionResponse


class MediaJobNotFoundError(Exception):
    pass


class MediaJobConflictError(Exception):
    pass


STAGE_PROGRESS = {
    "queued": 0,
    "converting": 15,
    "transcribing": 35,
    "generating": 70,
    "saving": 90,
    "complete": 100,
    "failed": 100,
    "canceled": 100,
}


def submit_media_job(
    upload_path: Path,
    project_name: str,
    provider: str = "deterministic",
    save_result: bool = True,
    language: str | None = None,
    settings: MediaSettings | None = None,
) -> MediaJobSubmissionResponse:
    media_settings = settings or get_media_settings()
    created_at = _utc_now_iso()
    metadata = {
        "status": "queued",
        "stage": "queued",
        "progress": STAGE_PROGRESS["queued"],
        "created_at": created_at,
        "upload_path": str(upload_path),
    }
    try:
        from backend.jobs.media_processing import process_media_job

        queue = get_media_queue(media_settings)
        job = queue.enqueue(
            process_media_job,
            str(upload_path),
            project_name,
            provider,
            save_result,
            language,
            job_timeout=media_settings.media_job_timeout_seconds,
            result_ttl=media_settings.media_job_result_ttl_seconds,
            failure_ttl=media_settings.media_job_failure_ttl_seconds,
            meta=metadata,
        )
    except (QueueConfigurationError, QueueUnavailableError):
        _delete_path(upload_path)
        raise
    except Exception as exc:
        _delete_path(upload_path)
        raise QueueUnavailableError("Redis is unavailable.") from exc

    return MediaJobSubmissionResponse(
        job_id=job.id,
        status="queued",
        stage="queued",
        created_at=datetime.fromisoformat(created_at),
    )


def get_media_job_status(job_id: str) -> MediaJobStatusResponse:
    job = _fetch_job(job_id)
    meta = job.meta if isinstance(job.meta, dict) else {}
    result = _job_result(job)
    if isinstance(result, dict) and result.get("status") in {"finished", "failed"}:
        meta = {**meta, **result}

    status = _safe_choice(meta.get("status"), {"queued", "started", "finished", "failed", "canceled"}, "queued")
    stage = _safe_choice(
        meta.get("stage"),
        {"queued", "converting", "transcribing", "generating", "saving", "complete", "failed", "canceled"},
        "queued",
    )
    return MediaJobStatusResponse(
        job_id=job.id,
        status=status,
        stage=stage,
        progress=_safe_progress(meta.get("progress"), stage),
        created_at=_safe_datetime(meta.get("created_at")),
        started_at=_optional_datetime(meta.get("started_at")),
        finished_at=_optional_datetime(meta.get("finished_at")),
        error=_safe_error(meta.get("error")),
        transcription=meta.get("transcription"),
        generation=meta.get("generation"),
        saved_generation_id=meta.get("saved_generation_id"),
    )


def cancel_media_job(job_id: str) -> None:
    job = _fetch_job(job_id)
    meta = job.meta if isinstance(job.meta, dict) else {}
    status = meta.get("status") or _string_status(job)
    if status != "queued":
        raise MediaJobConflictError("Media job cannot be canceled.")

    _delete_path(meta.get("upload_path"))
    try:
        job.cancel()
    except Exception as exc:
        raise QueueUnavailableError("Redis is unavailable.") from exc
    _update_job_meta(job, "canceled", "canceled")


def mark_job_stage(job, status: str, stage: str, extra: dict[str, Any] | None = None) -> None:
    _update_job_meta(job, status, stage, extra)


def _update_job_meta(job, status: str, stage: str, extra: dict[str, Any] | None = None) -> None:
    meta = dict(job.meta or {})
    meta.update(
        {
            "status": status,
            "stage": stage,
            "progress": STAGE_PROGRESS[stage],
        }
    )
    if status == "started" and "started_at" not in meta:
        meta["started_at"] = _utc_now_iso()
    if status in {"finished", "failed", "canceled"}:
        meta["finished_at"] = _utc_now_iso()
    if extra:
        meta.update(extra)
    job.meta = meta
    job.save_meta()


def _fetch_job(job_id: str):
    try:
        from rq.exceptions import NoSuchJobError
        from rq.job import Job
    except ImportError as exc:
        raise QueueConfigurationError("RQ dependency is not installed.") from exc

    try:
        return Job.fetch(job_id, connection=get_redis_connection())
    except NoSuchJobError as exc:
        raise MediaJobNotFoundError("Media job was not found.") from exc
    except (QueueConfigurationError, QueueUnavailableError):
        raise
    except Exception as exc:
        raise QueueUnavailableError("Redis is unavailable.") from exc


def _job_result(job):
    try:
        if hasattr(job, "return_value"):
            return job.return_value()
        return getattr(job, "result", None)
    except Exception:
        return None


def _string_status(job) -> str:
    try:
        status = job.get_status(refresh=True)
    except Exception:
        return "queued"
    return getattr(status, "value", str(status))


def _safe_choice(value, allowed: set[str], default: str) -> str:
    if isinstance(value, str) and value in allowed:
        return value
    return default


def _safe_progress(value, stage: str) -> int:
    if isinstance(value, int) and 0 <= value <= 100:
        return value
    return STAGE_PROGRESS.get(stage, 0)


def _safe_datetime(value) -> datetime:
    if isinstance(value, datetime):
        return value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value)
            return parsed.astimezone(UTC) if parsed.tzinfo else parsed.replace(tzinfo=UTC)
        except ValueError:
            pass
    return datetime.now(UTC)


def _optional_datetime(value) -> datetime | None:
    if value is None:
        return None
    return _safe_datetime(value)


def _safe_error(value) -> str | None:
    if isinstance(value, str) and value:
        return value
    return None


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _delete_path(path_value) -> None:
    if not path_value:
        return
    try:
        Path(path_value).unlink(missing_ok=True)
    except OSError:
        pass
