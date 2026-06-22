import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    ollama_base_url: str
    ollama_model: str
    ollama_timeout_seconds: float
    database_url: str = ""


@dataclass(frozen=True)
class RuntimeSettings:
    app_env: str
    log_level: str
    trusted_hosts: tuple[str, ...]
    security_headers_enabled: bool
    readiness_require_database: bool
    readiness_require_redis: bool


@dataclass(frozen=True)
class MediaSettings:
    redis_url: str
    rq_queue_name: str
    media_upload_dir: str
    media_max_upload_mb: int
    media_job_timeout_seconds: int
    media_job_result_ttl_seconds: int
    media_job_failure_ttl_seconds: int
    ffmpeg_executable: str
    whisper_cpp_executable: str
    whisper_cpp_model_path: str
    whisper_cpp_threads: int


def get_settings() -> Settings:
    timeout_value = os.getenv("OLLAMA_TIMEOUT_SECONDS", "60")
    try:
        timeout_seconds = float(timeout_value)
    except ValueError:
        timeout_seconds = 60.0

    return Settings(
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/"),
        ollama_model=os.getenv("OLLAMA_MODEL", ""),
        ollama_timeout_seconds=timeout_seconds,
        database_url=os.getenv("DATABASE_URL", ""),
    )


def get_runtime_settings() -> RuntimeSettings:
    return RuntimeSettings(
        app_env=os.getenv("APP_ENV", "development").strip() or "development",
        log_level=_log_level("LOG_LEVEL", "INFO"),
        trusted_hosts=_trusted_hosts(os.getenv("TRUSTED_HOSTS", "localhost,127.0.0.1,testserver")),
        security_headers_enabled=_bool("SECURITY_HEADERS_ENABLED", True),
        readiness_require_database=_bool("READINESS_REQUIRE_DATABASE", False),
        readiness_require_redis=_bool("READINESS_REQUIRE_REDIS", False),
    )


def get_media_settings() -> MediaSettings:
    return MediaSettings(
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        rq_queue_name=os.getenv("RQ_QUEUE_NAME", "media-processing"),
        media_upload_dir=os.getenv("MEDIA_UPLOAD_DIR", ".data/uploads"),
        media_max_upload_mb=_positive_int("MEDIA_MAX_UPLOAD_MB", 200),
        media_job_timeout_seconds=_positive_int("MEDIA_JOB_TIMEOUT_SECONDS", 3600),
        media_job_result_ttl_seconds=_positive_int("MEDIA_JOB_RESULT_TTL_SECONDS", 86400),
        media_job_failure_ttl_seconds=_positive_int("MEDIA_JOB_FAILURE_TTL_SECONDS", 86400),
        ffmpeg_executable=os.getenv("FFMPEG_EXECUTABLE", "ffmpeg"),
        whisper_cpp_executable=os.getenv("WHISPER_CPP_EXECUTABLE", ""),
        whisper_cpp_model_path=os.getenv("WHISPER_CPP_MODEL_PATH", ""),
        whisper_cpp_threads=_positive_int("WHISPER_CPP_THREADS", 4),
    )


def _positive_int(name: str, default: int) -> int:
    raw_value = os.getenv(name, str(default))
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a positive integer.") from exc
    if value <= 0:
        raise ValueError(f"{name} must be a positive integer.")
    return value


def _log_level(name: str, default: str) -> str:
    value = os.getenv(name, default).strip().upper()
    allowed_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if value not in allowed_levels:
        raise ValueError(f"{name} must be one of: {', '.join(sorted(allowed_levels))}.")
    return value


def _bool(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    normalized_value = raw_value.strip().casefold()
    if normalized_value in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized_value in {"0", "false", "no", "n", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean value.")


def _trusted_hosts(raw_value: str) -> tuple[str, ...]:
    seen_hosts: set[str] = set()
    trusted_hosts: list[str] = []
    for host in raw_value.split(","):
        normalized_host = host.strip()
        if not normalized_host or normalized_host in seen_hosts:
            continue
        seen_hosts.add(normalized_host)
        trusted_hosts.append(normalized_host)

    if "testserver" not in seen_hosts:
        trusted_hosts.append("testserver")

    return tuple(trusted_hosts)
