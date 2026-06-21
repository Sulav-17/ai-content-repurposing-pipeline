from fastapi.testclient import TestClient

from backend.main import app
from backend.providers.base import ProviderUnavailableError
from backend.services import content_brief_service


client = TestClient(app)


def test_content_brief_deterministic_request_returns_200() -> None:
    response = client.post(
        "/content/brief",
        json={
            "text": "Host: Python API wins. Guest: Python content works.",
            "provider": "deterministic",
        },
    )

    assert response.status_code == 200


def test_content_brief_response_has_complete_expected_structure() -> None:
    response = client.post(
        "/content/brief",
        json={"text": "Host: Python API wins."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "deterministic"
    assert body["cleaned_text"] == "Host: Python API wins."
    assert body["metadata"]["line_count"] == 1
    assert body["analysis"]["sentence_count"] == 1
    assert body["analysis"]["key_points"] == ["Host: Python API wins."]
    assert body["brief"] == {
        "summary": "Grounded brief based on the transcript: Host: Python API wins.",
        "core_message": "The transcript emphasizes: Host: Python API wins.",
        "target_audience": "General audience (deterministic default)",
        "key_takeaways": ["Host: Python API wins."],
        "suggested_tone": "Clear and practical (deterministic default)",
        "source_keywords": ["api", "host", "python", "wins"],
    }


def test_content_brief_default_provider_is_deterministic() -> None:
    response = client.post(
        "/content/brief",
        json={"text": "Host: Python API wins."},
    )

    assert response.status_code == 200
    assert response.json()["provider"] == "deterministic"


def test_content_brief_cleans_transcript_before_generation() -> None:
    response = client.post(
        "/content/brief",
        json={"text": "  Host:\tPython   API wins.  "},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["cleaned_text"] == "Host: Python API wins."
    assert body["metadata"]["changed"] is True
    assert body["brief"]["key_takeaways"] == ["Host: Python API wins."]


def test_content_brief_includes_analysis() -> None:
    response = client.post(
        "/content/brief",
        json={"text": "Host: Python API wins. Guest: Python content works."},
    )

    analysis = response.json()["analysis"]
    assert response.status_code == 200
    assert analysis["top_keywords"][0] == {"term": "python", "count": 2}
    assert analysis["key_points"] == [
        "Host: Python API wins.",
        "Guest: Python content works.",
    ]


def test_content_brief_returns_422_for_missing_text() -> None:
    response = client.post("/content/brief", json={})

    assert response.status_code == 422


def test_content_brief_returns_422_for_whitespace_only_text() -> None:
    response = client.post("/content/brief", json={"text": " \n\t "})

    assert response.status_code == 422


def test_content_brief_returns_422_for_oversized_text() -> None:
    response = client.post("/content/brief", json={"text": "a" * 200_001})

    assert response.status_code == 422


def test_content_brief_returns_422_for_invalid_provider() -> None:
    response = client.post(
        "/content/brief",
        json={"text": "Host: Python API wins.", "provider": "openai"},
    )

    assert response.status_code == 422


def test_content_brief_maps_unavailable_ollama_to_503(monkeypatch) -> None:
    def fake_generate_content_brief(*args, **kwargs):
        raise ProviderUnavailableError("Ollama is unavailable.")

    monkeypatch.setattr(
        content_brief_service,
        "generate_content_brief",
        fake_generate_content_brief,
    )

    response = client.post(
        "/content/brief",
        json={"text": "Host: Python API wins.", "provider": "ollama"},
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "Ollama is unavailable."}
