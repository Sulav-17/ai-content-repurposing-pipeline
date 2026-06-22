from typing import Literal

from sqlalchemy import create_engine, text

from backend.core.config import RuntimeSettings, get_media_settings, get_runtime_settings, get_settings


ReadinessState = Literal["ready", "unavailable", "skipped"]


def readiness_checks(runtime_settings: RuntimeSettings | None = None) -> dict[str, ReadinessState]:
    settings = runtime_settings or get_runtime_settings()
    return {
        "database": _database_check(settings),
        "redis": _redis_check(settings),
    }


def is_ready(checks: dict[str, ReadinessState]) -> bool:
    return all(state != "unavailable" for state in checks.values())


def _database_check(settings: RuntimeSettings) -> ReadinessState:
    if not settings.readiness_require_database:
        return "skipped"

    database_url = get_settings().database_url
    if not database_url:
        return "unavailable"

    connect_args = {"connect_timeout": 2}
    if database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False, "timeout": 2}

    engine = None
    try:
        engine = create_engine(
            database_url,
            connect_args=connect_args,
            pool_pre_ping=True,
        )
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        return "unavailable"
    finally:
        if engine is not None:
            engine.dispose()

    return "ready"


def _redis_check(settings: RuntimeSettings) -> ReadinessState:
    if not settings.readiness_require_redis:
        return "skipped"

    redis_url = get_media_settings().redis_url
    if not redis_url:
        return "unavailable"

    try:
        from redis import Redis

        redis_client = Redis.from_url(
            redis_url,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        try:
            redis_client.ping()
        finally:
            redis_client.close()
    except Exception:
        return "unavailable"

    return "ready"
