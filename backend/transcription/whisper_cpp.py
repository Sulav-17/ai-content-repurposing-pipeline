import json
import re
import subprocess
from pathlib import Path
from uuid import uuid4

from pydantic import ValidationError

from backend.core.config import MediaSettings, get_media_settings
from backend.schemas.media_jobs import TranscriptionResult, TranscriptionSegment
from backend.transcription.base import TranscriptionConfigurationError, TranscriptionError


class WhisperCppTranscriber:
    def __init__(self, settings: MediaSettings | None = None) -> None:
        self.settings = settings or get_media_settings()

    def transcribe(
        self,
        media_path: Path | str,
        language: str | None = None,
    ) -> TranscriptionResult:
        self._validate_configuration()
        source_path = Path(media_path)
        output_prefix = source_path.with_name(f"{source_path.stem}-whisper-{uuid4().hex}")
        json_path = output_prefix.with_suffix(".json")
        command = [
            self.settings.whisper_cpp_executable,
            "--model",
            self.settings.whisper_cpp_model_path,
            "--file",
            str(source_path),
            "--output-json-full",
            "--output-file",
            str(output_prefix),
            "--threads",
            str(self.settings.whisper_cpp_threads),
        ]
        if language and language.strip():
            command.extend(["--language", language.strip()])

        try:
            result = subprocess.run(
                command,
                shell=False,
                capture_output=True,
                text=True,
                timeout=self.settings.media_job_timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            self._cleanup_outputs(output_prefix)
            raise TranscriptionError("Transcription timed out.") from exc
        except OSError as exc:
            self._cleanup_outputs(output_prefix)
            raise TranscriptionError("Transcription failed.") from exc

        try:
            if result.returncode != 0:
                raise TranscriptionError("Transcription failed.")
            return self._parse_json_file(json_path, language)
        finally:
            self._cleanup_outputs(output_prefix)

    def _validate_configuration(self) -> None:
        executable = self.settings.whisper_cpp_executable.strip()
        model_path = self.settings.whisper_cpp_model_path.strip()
        if not executable or not Path(executable).is_file():
            raise TranscriptionConfigurationError("whisper.cpp executable is not configured.")
        if not model_path or not Path(model_path).is_file():
            raise TranscriptionConfigurationError("whisper.cpp model is not configured.")

    def _parse_json_file(
        self,
        json_path: Path,
        language: str | None,
    ) -> TranscriptionResult:
        if not json_path.exists():
            raise TranscriptionError("Transcription output was missing.")

        try:
            raw_json = json_path.read_bytes().decode("utf-8")
        except UnicodeDecodeError as exc:
            raise TranscriptionError("Transcription output was malformed.") from exc
        except OSError as exc:
            raise TranscriptionError("Transcription output was missing.") from exc

        try:
            payload = json.loads(raw_json)
        except json.JSONDecodeError as exc:
            raise TranscriptionError("Transcription output was malformed.") from exc

        transcription = payload.get("transcription") if isinstance(payload, dict) else None
        if not isinstance(transcription, list):
            raise TranscriptionError("Transcription output was malformed.")

        segments: list[TranscriptionSegment] = []
        for item in transcription:
            segments.append(_segment_from_payload(item))

        lines = [
            f"[{_format_timestamp(segment.start_seconds)}] {segment.text}"
            for segment in segments
        ]
        normalized_text = "\n".join(lines).strip()
        if not normalized_text:
            raise TranscriptionError("Transcription output was blank.")

        try:
            return TranscriptionResult(
                text=normalized_text,
                segments=segments,
                language=language,
            )
        except ValidationError as exc:
            raise TranscriptionError("Transcription output was malformed.") from exc

    def _cleanup_outputs(self, output_prefix: Path) -> None:
        for path in output_prefix.parent.glob(f"{output_prefix.name}*"):
            if path.is_file():
                try:
                    path.unlink()
                except OSError:
                    pass


def _segment_from_payload(payload) -> TranscriptionSegment:
    if not isinstance(payload, dict):
        raise TranscriptionError("Transcription output was malformed.")

    text = " ".join(str(payload.get("text", "")).split())
    if not text:
        raise TranscriptionError("Transcription output was blank.")

    timestamps = payload.get("timestamps")
    if isinstance(timestamps, dict):
        start_value = timestamps.get("from")
        end_value = timestamps.get("to")
    else:
        offsets = payload.get("offsets")
        if isinstance(offsets, dict):
            start_value = offsets.get("from")
            end_value = offsets.get("to")
        else:
            start_value = payload.get("start")
            end_value = payload.get("end")

    try:
        start_seconds = _parse_timestamp(start_value)
        end_seconds = _parse_timestamp(end_value)
        return TranscriptionSegment(
            start_seconds=start_seconds,
            end_seconds=end_seconds,
            text=text,
        )
    except (TypeError, ValueError, ValidationError) as exc:
        raise TranscriptionError("Transcription output was malformed.") from exc


def _parse_timestamp(value) -> float:
    if isinstance(value, (int, float)):
        if value < 0:
            raise ValueError("timestamp must be nonnegative")
        return float(value)
    if not isinstance(value, str):
        raise ValueError("timestamp is missing")

    timestamp = value.strip().replace(",", ".")
    if not timestamp:
        raise ValueError("timestamp is missing")
    if re.fullmatch(r"\d+(\.\d+)?", timestamp):
        return float(timestamp)

    parts = timestamp.split(":")
    if len(parts) not in (2, 3):
        raise ValueError("timestamp is malformed")
    seconds = float(parts[-1])
    minutes = int(parts[-2])
    hours = int(parts[-3]) if len(parts) == 3 else 0
    return (hours * 3600) + (minutes * 60) + seconds


def _format_timestamp(seconds: float) -> str:
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    remaining_seconds = total_seconds % 60
    if hours:
        return f"{hours:02d}:{minutes:02d}:{remaining_seconds:02d}"
    return f"{minutes:02d}:{remaining_seconds:02d}"
