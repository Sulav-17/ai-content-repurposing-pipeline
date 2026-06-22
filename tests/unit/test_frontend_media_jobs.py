import httpx
import pytest

from frontend import renderers
from frontend.api_client import ApiClient, ApiRequestError, validate_media_job_status_response
from tests.unit.test_frontend_api_client import generation_payload, make_client


def media_status_payload() -> dict:
    return {
        "job_id": "job-1",
        "status": "finished",
        "stage": "complete",
        "progress": 100,
        "created_at": "2026-01-01T00:00:00Z",
        "started_at": None,
        "finished_at": "2026-01-01T00:01:00Z",
        "error": None,
        "transcription": {"text": "[00:05] Hello.", "segments": [], "language": "en"},
        "generation": generation_payload(),
        "saved_generation_id": "saved-1",
    }


def test_api_client_submits_multipart_media_job() -> None:
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        seen["content_type"] = request.headers["content-type"]
        seen["body"] = request.content
        return httpx.Response(
            202,
            json={
                "job_id": "job-1",
                "status": "queued",
                "stage": "queued",
                "created_at": "2026-01-01T00:00:00Z",
            },
        )

    client = make_client(handler)

    response = client.submit_media_job(
        file_name="clip.mp3",
        file_bytes=b"media",
        content_type="audio/mpeg",
        project_name="Demo",
    )

    assert response["job_id"] == "job-1"
    assert seen["method"] == "POST"
    assert seen["path"] == "/media-jobs"
    assert "multipart/form-data" in seen["content_type"]
    assert b"clip.mp3" in seen["body"]


def test_api_client_retrieves_and_cancels_media_job() -> None:
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        if request.method == "GET":
            return httpx.Response(200, json=media_status_payload())
        return httpx.Response(204)

    client = make_client(handler)

    assert client.get_media_job("job-1")["stage"] == "complete"
    assert client.cancel_media_job("job-1") is None
    assert seen == [("GET", "/media-jobs/job-1"), ("DELETE", "/media-jobs/job-1")]


def test_api_client_maps_media_job_conflicts_and_oversized_uploads() -> None:
    conflict_client = make_client(lambda request: httpx.Response(409, json={"detail": "secret"}))
    too_large_client = make_client(lambda request: httpx.Response(413, json={"detail": "secret"}))

    with pytest.raises(ApiRequestError, match="conflicts"):
        conflict_client.cancel_media_job("job-1")
    with pytest.raises(ApiRequestError, match="too large"):
        too_large_client.submit_media_job("clip.mp3", b"x", "audio/mpeg", "Demo")


def test_media_job_status_validation_rejects_malformed_payloads() -> None:
    with pytest.raises(Exception):
        validate_media_job_status_response({"job_id": "job-1"})


def test_media_job_renderer_displays_status_without_backend_imports(monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(renderers.st, "markdown", lambda value: calls.append(("markdown", value)))
    monkeypatch.setattr(renderers.st, "write", lambda value: calls.append(("write", value)))
    monkeypatch.setattr(renderers.st, "progress", lambda value: calls.append(("progress", value)))
    monkeypatch.setattr(renderers.st, "caption", lambda value: calls.append(("caption", value)))
    monkeypatch.setattr(renderers.st, "error", lambda value: calls.append(("error", value)))
    monkeypatch.setattr(renderers.st, "text_area", lambda *args, **kwargs: calls.append(("text_area", args[0])))

    class FakeExpander:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

    monkeypatch.setattr(renderers.st, "expander", lambda *args, **kwargs: FakeExpander())
    monkeypatch.setattr(renderers, "render_generation_result", lambda result: calls.append(("generation", result["project_name"])))

    renderers.render_media_job_status(media_status_payload())

    assert ("write", "Status: finished") in calls
    assert ("progress", 100) in calls
    assert ("generation", "Demo") in calls
