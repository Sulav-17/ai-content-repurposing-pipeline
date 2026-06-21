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
