from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import app
from backend.queueing.connection import QueueUnavailableError
from backend.schemas.media_jobs import MediaJobSubmissionResponse, MediaJobStatusResponse
from backend.services import media_job_service
from backend.services.media_job_service import MediaJobConflictError, MediaJobNotFoundError
from backend.services.media_upload_service import UploadTooLargeError


client = TestClient(app)


def test_submit_media_job_returns_202(monkeypatch, tmp_path) -> None:
    upload_path = tmp_path / "upload.mp3"

    async def fake_save_upload(file):
        return upload_path

    def fake_submit_media_job(**kwargs):
        assert kwargs["upload_path"] == upload_path
        assert kwargs["project_name"] == "Demo"
        assert kwargs["provider"] == "deterministic"
        assert kwargs["save_result"] is True
        return MediaJobSubmissionResponse(
            job_id="job-1",
            status="queued",
            stage="queued",
            created_at=datetime.now(UTC),
        )

    monkeypatch.setattr("backend.api.routes.media_jobs.save_upload", fake_save_upload)
    monkeypatch.setattr(media_job_service, "submit_media_job", fake_submit_media_job)

    response = client.post(
        "/media-jobs",
        data={"project_name": " Demo ", "provider": "deterministic", "save_result": "true"},
        files={"file": ("clip.mp3", b"media", "audio/mpeg")},
    )

    assert response.status_code == 202
    assert response.json()["job_id"] == "job-1"


def test_submit_media_job_maps_413_and_503(monkeypatch) -> None:
    async def too_large(file):
        raise UploadTooLargeError()

    monkeypatch.setattr("backend.api.routes.media_jobs.save_upload", too_large)
    response = client.post(
        "/media-jobs",
        data={"project_name": "Demo"},
        files={"file": ("clip.mp3", b"media", "audio/mpeg")},
    )
    assert response.status_code == 413

    async def saved(file):
        return Path("upload.mp3")

    monkeypatch.setattr("backend.api.routes.media_jobs.save_upload", saved)
    monkeypatch.setattr(media_job_service, "submit_media_job", lambda **kwargs: (_ for _ in ()).throw(QueueUnavailableError()))

    response = client.post(
        "/media-jobs",
        data={"project_name": "Demo"},
        files={"file": ("clip.mp3", b"media", "audio/mpeg")},
    )
    assert response.status_code == 503
    assert "redis://" not in response.text


def test_media_job_status_and_cancellation(monkeypatch) -> None:
    monkeypatch.setattr(
        media_job_service,
        "get_media_job_status",
        lambda job_id: MediaJobStatusResponse(
            job_id=job_id,
            status="started",
            stage="generating",
            progress=70,
            created_at=datetime.now(UTC),
        ),
    )

    response = client.get("/media-jobs/job-1")
    assert response.status_code == 200
    assert response.json()["stage"] == "generating"

    monkeypatch.setattr(media_job_service, "cancel_media_job", lambda job_id: None)
    assert client.delete("/media-jobs/job-1").status_code == 204


def test_media_job_unknown_and_conflict(monkeypatch) -> None:
    monkeypatch.setattr(
        media_job_service,
        "get_media_job_status",
        lambda job_id: (_ for _ in ()).throw(MediaJobNotFoundError()),
    )
    assert client.get("/media-jobs/missing").status_code == 404

    monkeypatch.setattr(
        media_job_service,
        "cancel_media_job",
        lambda job_id: (_ for _ in ()).throw(MediaJobConflictError()),
    )
    assert client.delete("/media-jobs/job-1").status_code == 409
