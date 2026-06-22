from pathlib import Path
from typing import Protocol

from backend.schemas.media_jobs import TranscriptionResult


class TranscriptionConfigurationError(Exception):
    pass


class TranscriptionError(Exception):
    pass


class Transcriber(Protocol):
    def transcribe(
        self,
        media_path: Path | str,
        language: str | None = None,
    ) -> TranscriptionResult:
        ...
