import os
from dataclasses import dataclass
from urllib.parse import urlparse

from dotenv import load_dotenv


class FrontendConfigurationError(Exception):
    pass


@dataclass(frozen=True)
class FrontendSettings:
    api_base_url: str
    api_timeout_seconds: float


def get_frontend_settings() -> FrontendSettings:
    load_dotenv()
    base_url = _validate_base_url(
        os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
    )
    timeout_seconds = _validate_timeout(
        os.getenv("API_TIMEOUT_SECONDS", "30")
    )
    return FrontendSettings(
        api_base_url=base_url,
        api_timeout_seconds=timeout_seconds,
    )


def _validate_base_url(value: str) -> str:
    stripped_value = value.strip().rstrip("/")
    parsed_url = urlparse(stripped_value)
    if parsed_url.scheme not in {"http", "https"}:
        raise FrontendConfigurationError("API base URL must use HTTP or HTTPS.")
    if not parsed_url.netloc:
        raise FrontendConfigurationError("API base URL must include a host.")
    if parsed_url.username or parsed_url.password:
        raise FrontendConfigurationError("API base URL must not include credentials.")
    return stripped_value


def _validate_timeout(value: str) -> float:
    try:
        timeout_seconds = float(value)
    except ValueError as exc:
        raise FrontendConfigurationError("API timeout must be a positive number.") from exc

    if timeout_seconds <= 0:
        raise FrontendConfigurationError("API timeout must be positive.")
    return timeout_seconds
