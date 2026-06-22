from datetime import UTC, datetime
from pathlib import Path

import pytest

from backend.core.config import MediaSettings
from backend.queueing.connection import QueueUnavailableError
from backend.services import media_job_service
from backend.services.media_job_service import MediaJobConflictError


class FakeQueue:
    def __init__(self) -> None:
        self.kwargs = None

    def enqueue(self, func, *args, **kwargs):
        self.kwargs = kwargs
        return FakeJob("job-1", kwargs["meta"])


class FakeJob:
    def __init__(self, job_id="job-1", meta=None) -> None:
        self.id = job_id
        self.meta = meta or {}
        self.saved = 0
        self.canceled = False

    def save_meta(self):
        self.saved += 1

    def cancel(self):
        self.canceled = True

    def return_value(self):
        return None


def settings() -> MediaSettings:
    return MediaSettings(
        redis_url="redis://localhost:6379/0",
        rq_queue_name="media-processing",
        media_upload_dir=".data/uploads",
        media_max_upload_mb=200,
        media_job_timeout_seconds=123,
        media_job_result_ttl_seconds=456,
        media_job_failure_ttl_seconds=789,
        ffmpeg_executable="ffmpeg",
        whisper_cpp_executable="whisper",
        whisper_cpp_model_path="model.bin",
        whisper_cpp_threads=4,
    )


def test_submit_media_job_uses_ttl_timeout_and_safe_metadata(monkeypatch, tmp_path) -> None:
    queue = FakeQueue()
    upload_path = tmp_path / "upload.mp3"
    upload_path.write_bytes(b"media")
    monkeypatch.setattr(media_job_service, "get_media_queue", lambda media_settings: queue)

    response = media_job_service.submit_media_job(upload_path, "Demo", settings=settings())

    assert response.job_id == "job-1"
    assert queue.kwargs["job_timeout"] == 123
    assert queue.kwargs["result_ttl"] == 456
    assert queue.kwargs["failure_ttl"] == 789
    assert queue.kwargs["meta"]["status"] == "queued"
    assert queue.kwargs["meta"]["progress"] == 0


def test_submit_media_job_deletes_upload_when_enqueue_fails(monkeypatch, tmp_path) -> None:
    upload_path = tmp_path / "upload.mp3"
    upload_path.write_bytes(b"media")
    monkeypatch.setattr(media_job_service, "get_media_queue", lambda media_settings: (_ for _ in ()).throw(QueueUnavailableError()))

    with pytest.raises(QueueUnavailableError):
        media_job_service.submit_media_job(upload_path, "Demo", settings=settings())

    assert not upload_path.exists()


def test_status_response_uses_safe_allowlist(monkeypatch) -> None:
    job = FakeJob(
        meta={
            "status": "started",
            "stage": "transcribing",
            "progress": 35,
            "created_at": datetime.now(UTC).isoformat(),
            "upload_path": "secret",
            "error": "safe",
        }
    )
    monkeypatch.setattr(media_job_service, "_fetch_job", lambda job_id: job)

    response = media_job_service.get_media_job_status("job-1")

    assert response.status == "started"
    assert response.stage == "transcribing"
    assert response.progress == 35
    assert response.error == "safe"
    assert not hasattr(response, "upload_path")


def test_cancel_only_allows_queued_jobs(monkeypatch, tmp_path) -> None:
    upload_path = tmp_path / "upload.mp3"
    upload_path.write_bytes(b"media")
    queued_job = FakeJob(meta={"status": "queued", "stage": "queued", "upload_path": str(upload_path)})
    monkeypatch.setattr(media_job_service, "_fetch_job", lambda job_id: queued_job)

    media_job_service.cancel_media_job("job-1")

    assert queued_job.canceled is True
    assert queued_job.meta["status"] == "canceled"
    assert queued_job.saved == 1
    assert not upload_path.exists()

    monkeypatch.setattr(media_job_service, "_fetch_job", lambda job_id: FakeJob(meta={"status": "started"}))
    with pytest.raises(MediaJobConflictError):
        media_job_service.cancel_media_job("job-1")
