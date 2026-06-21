from fastapi.testclient import TestClient

from backend.main import app


def test_health_endpoint_returns_expected_response() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "ai-content-repurposing-pipeline",
    }
