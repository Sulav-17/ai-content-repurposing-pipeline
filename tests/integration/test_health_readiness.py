import sys
from types import SimpleNamespace

from fastapi.testclient import TestClient

from backend.core.config import RuntimeSettings
from backend.main import create_app
from backend.services import readiness_service


def runtime_settings(
    *,
    security_headers_enabled: bool = True,
    readiness_require_database: bool = False,
    readiness_require_redis: bool = False,
) -> RuntimeSettings:
    return RuntimeSettings(
        app_env="test",
        log_level="INFO",
        trusted_hosts=("testserver", "localhost", "127.0.0.1", "api"),
        security_headers_enabled=security_headers_enabled,
        readiness_require_database=readiness_require_database,
        readiness_require_redis=readiness_require_redis,
    )


def test_existing_health_endpoint_is_unchanged() -> None:
    client = TestClient(create_app(runtime_settings=runtime_settings()))

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "ai-content-repurposing-pipeline",
    }


def test_liveness_endpoint_performs_no_dependency_checks(monkeypatch) -> None:
    monkeypatch.setattr(
        "backend.api.routes.health.readiness_checks",
        lambda: (_ for _ in ()).throw(AssertionError("readiness should not run")),
    )
    client = TestClient(create_app(runtime_settings=runtime_settings()))

    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {
        "status": "alive",
        "service": "ai-content-repurposing-pipeline",
    }


def test_ready_endpoint_returns_healthy_mocked_dependencies(monkeypatch) -> None:
    monkeypatch.setattr(
        "backend.api.routes.health.readiness_checks",
        lambda runtime_settings=None: {"database": "ready", "redis": "ready"},
    )
    client = TestClient(create_app(runtime_settings=runtime_settings()))

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "checks": {"database": "ready", "redis": "ready"},
    }


def test_readiness_skips_optional_dependencies() -> None:
    checks = readiness_service.readiness_checks(runtime_settings())

    assert checks == {"database": "skipped", "redis": "skipped"}


def test_required_database_unavailable_returns_503(monkeypatch) -> None:
    monkeypatch.setattr(readiness_service, "get_settings", lambda: SimpleNamespace(database_url=""))
    client = TestClient(
        create_app(
            runtime_settings=runtime_settings(
                readiness_require_database=True,
                readiness_require_redis=False,
            )
        )
    )

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "checks": {"database": "unavailable", "redis": "skipped"},
    }
    assert "postgresql://" not in response.text
    assert "SELECT 1" not in response.text


def test_required_redis_unavailable_returns_503(monkeypatch) -> None:
    monkeypatch.setattr(readiness_service, "get_media_settings", lambda: SimpleNamespace(redis_url=""))
    client = TestClient(
        create_app(
            runtime_settings=runtime_settings(
                readiness_require_database=False,
                readiness_require_redis=True,
            )
        )
    )

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "checks": {"database": "skipped", "redis": "unavailable"},
    }
    assert "redis://" not in response.text


def test_readiness_service_uses_mocked_database_and_redis(monkeypatch) -> None:
    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def execute(self, statement):
            return None

    class FakeEngine:
        def connect(self):
            return FakeConnection()

        def dispose(self):
            return None

    class FakeRedis:
        @classmethod
        def from_url(cls, url, socket_connect_timeout, socket_timeout):
            return cls()

        def ping(self):
            return True

        def close(self):
            return None

    monkeypatch.setattr(readiness_service, "get_settings", lambda: SimpleNamespace(database_url="postgresql://secret"))
    monkeypatch.setattr(readiness_service, "get_media_settings", lambda: SimpleNamespace(redis_url="redis://secret"))
    monkeypatch.setattr(readiness_service, "create_engine", lambda *args, **kwargs: FakeEngine())
    monkeypatch.setitem(sys.modules, "redis", SimpleNamespace(Redis=FakeRedis))

    checks = readiness_service.readiness_checks(
        runtime_settings(
            readiness_require_database=True,
            readiness_require_redis=True,
        )
    )

    assert checks == {"database": "ready", "redis": "ready"}


def test_security_headers_enabled_on_success_and_handled_error() -> None:
    client = TestClient(create_app(runtime_settings=runtime_settings(security_headers_enabled=True)))

    success_response = client.get("/health")
    error_response = client.get("/generations/missing")

    for response in [success_response, error_response]:
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["Referrer-Policy"] == "no-referrer"


def test_security_headers_can_be_disabled() -> None:
    client = TestClient(create_app(runtime_settings=runtime_settings(security_headers_enabled=False)))

    response = client.get("/health")

    assert "X-Content-Type-Options" not in response.headers
    assert "X-Frame-Options" not in response.headers
    assert "Referrer-Policy" not in response.headers


def test_existing_endpoint_still_functions_with_hardening() -> None:
    client = TestClient(create_app(runtime_settings=runtime_settings()))

    response = client.post("/transcripts/clean", json={"text": "  Hello   world.  "})

    assert response.status_code == 200
    assert response.json()["cleaned_text"] == "Hello world."
