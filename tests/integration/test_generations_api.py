from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.database.base import Base
from backend.database.session import get_db_session, reset_engine_cache
from backend.main import app


@pytest.fixture
def client_with_database(tmp_path) -> Generator[TestClient, None, None]:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'api.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

    def override_get_db_session() -> Generator[Session, None, None]:
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db_session] = override_get_db_session
    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
    engine.dispose()


def generation_payload(project_name: str = "Demo") -> dict[str, str]:
    return {
        "text": "Host: Python API wins. Guest: Python content works.",
        "project_name": project_name,
    }


def test_post_generations_returns_201_and_complete_saved_response(client_with_database) -> None:
    response = client_with_database.post("/generations", json=generation_payload())

    body = response.json()
    assert response.status_code == 201
    assert body["id"]
    assert body["created_at"]
    assert body["generation"]["project_name"] == "Demo"
    assert body["generation"]["assets"]["project_summary"]
    assert body["generation"]["markdown_export"]


def test_post_generations_default_deterministic_provider_works(client_with_database) -> None:
    response = client_with_database.post("/generations", json=generation_payload())

    assert response.status_code == 201
    assert response.json()["generation"]["provider"] == "deterministic"


def test_get_generations_returns_summaries_with_pagination(client_with_database) -> None:
    first = client_with_database.post("/generations", json=generation_payload("First")).json()
    second = client_with_database.post("/generations", json=generation_payload("Second")).json()

    response = client_with_database.get("/generations", params={"limit": 1, "offset": 0})

    body = response.json()
    assert response.status_code == 200
    assert body["total"] == 2
    assert body["limit"] == 1
    assert body["offset"] == 0
    assert len(body["items"]) == 1
    assert body["items"][0]["id"] in {first["id"], second["id"]}
    assert "input_text" not in body["items"][0]
    assert "markdown_export" not in body["items"][0]


def test_get_generations_pagination_second_page(client_with_database) -> None:
    client_with_database.post("/generations", json=generation_payload("First"))
    client_with_database.post("/generations", json=generation_payload("Second"))

    response = client_with_database.get("/generations", params={"limit": 1, "offset": 1})

    assert response.status_code == 200
    assert len(response.json()["items"]) == 1


def test_get_generation_returns_full_record(client_with_database) -> None:
    saved = client_with_database.post("/generations", json=generation_payload()).json()

    response = client_with_database.get(f"/generations/{saved['id']}")

    assert response.status_code == 200
    assert response.json()["generation"]["markdown_export"]
    assert response.json()["generation"]["cleaned_text"]


def test_get_missing_generation_returns_404(client_with_database) -> None:
    response = client_with_database.get("/generations/missing")

    assert response.status_code == 404
    assert response.json() == {"detail": "Generation was not found."}


def test_delete_generation_returns_204_and_later_404(client_with_database) -> None:
    saved = client_with_database.post("/generations", json=generation_payload()).json()

    delete_response = client_with_database.delete(f"/generations/{saved['id']}")
    get_response = client_with_database.get(f"/generations/{saved['id']}")

    assert delete_response.status_code == 204
    assert get_response.status_code == 404


def test_missing_database_configuration_returns_503(monkeypatch) -> None:
    app.dependency_overrides.clear()
    monkeypatch.delenv("DATABASE_URL", raising=False)
    reset_engine_cache()

    with TestClient(app) as client:
        response = client.post("/generations", json=generation_payload())

    assert response.status_code == 503
    assert response.json() == {"detail": "Database configuration is missing."}


def test_invalid_generation_request_values_return_422(client_with_database) -> None:
    response = client_with_database.post(
        "/generations",
        json={"text": " \n\t ", "project_name": "Demo"},
    )

    assert response.status_code == 422


def test_previous_endpoints_remain_functional(client_with_database) -> None:
    assert client_with_database.get("/health").status_code == 200
    assert client_with_database.post("/transcripts/clean", json={"text": "Host: Hi."}).status_code == 200
    assert client_with_database.post("/transcripts/analyze", json={"text": "Host: Hi."}).status_code == 200
    assert client_with_database.post("/content/brief", json={"text": "Host: Hi."}).status_code == 200
    assert client_with_database.post(
        "/content/generate",
        json={"text": "Host: Hi.", "project_name": "Demo"},
    ).status_code == 200
