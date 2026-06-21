from fastapi.testclient import TestClient

from backend.main import app
from backend.providers.base import ProviderResponseError, ProviderUnavailableError
from backend.services import content_generation_service


client = TestClient(app)


def test_generation_default_deterministic_request_returns_200() -> None:
    response = client.post(
        "/content/generate",
        json={
            "text": "Host: Python API wins. Guest: Python content works.",
            "project_name": "Demo Project",
        },
    )

    assert response.status_code == 200
    assert response.json()["provider"] == "deterministic"


def test_generation_response_has_complete_structure_counts_and_markdown() -> None:
    response = client.post(
        "/content/generate",
        json={
            "text": "[00:05] Host: Python API wins. Guest: Python content works.",
            "project_name": "Demo Project",
        },
    )

    body = response.json()
    assert response.status_code == 200
    assert body["project_name"] == "Demo Project"
    assert body["cleaned_text"]
    assert body["metadata"]
    assert body["analysis"]
    assert body["brief"]
    assert len(body["assets"]["youtube_titles"]) == 5
    assert len(body["assets"]["short_hooks"]) == 5
    assert body["assets"]["youtube_chapters"][0]["timestamp"] == "00:05"
    assert "# Demo Project" in body["markdown_export"]


def test_generation_project_name_validation() -> None:
    blank_response = client.post(
        "/content/generate",
        json={"text": "Host: Python API wins.", "project_name": "   "},
    )
    long_response = client.post(
        "/content/generate",
        json={"text": "Host: Python API wins.", "project_name": "x" * 121},
    )

    assert blank_response.status_code == 422
    assert long_response.status_code == 422


def test_generation_transcript_validation() -> None:
    missing_response = client.post(
        "/content/generate",
        json={"project_name": "Demo"},
    )
    whitespace_response = client.post(
        "/content/generate",
        json={"text": " \n\t ", "project_name": "Demo"},
    )

    assert missing_response.status_code == 422
    assert whitespace_response.status_code == 422


def test_generation_invalid_provider_returns_422() -> None:
    response = client.post(
        "/content/generate",
        json={
            "text": "Host: Python API wins.",
            "project_name": "Demo",
            "provider": "openai",
        },
    )

    assert response.status_code == 422


def test_generation_maps_unavailable_provider_to_503(monkeypatch) -> None:
    def fake_generate_content_assets(*args, **kwargs):
        raise ProviderUnavailableError("Ollama is unavailable.")

    monkeypatch.setattr(
        content_generation_service,
        "generate_content_assets",
        fake_generate_content_assets,
    )

    response = client.post(
        "/content/generate",
        json={
            "text": "Host: Python API wins.",
            "project_name": "Demo",
            "provider": "ollama",
        },
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "Ollama is unavailable."}


def test_generation_maps_invalid_provider_output_to_502(monkeypatch) -> None:
    def fake_generate_content_assets(*args, **kwargs):
        raise ProviderResponseError("Invalid provider output.")

    monkeypatch.setattr(
        content_generation_service,
        "generate_content_assets",
        fake_generate_content_assets,
    )

    response = client.post(
        "/content/generate",
        json={
            "text": "Host: Python API wins.",
            "project_name": "Demo",
            "provider": "ollama",
        },
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "Invalid provider output."}


def test_existing_endpoints_remain_functional() -> None:
    assert client.get("/health").status_code == 200
    assert client.post("/transcripts/clean", json={"text": "Host: Hi."}).status_code == 200
    assert client.post("/transcripts/analyze", json={"text": "Host: Hi."}).status_code == 200
    assert client.post("/content/brief", json={"text": "Host: Hi."}).status_code == 200
