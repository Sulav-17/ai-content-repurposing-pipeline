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
