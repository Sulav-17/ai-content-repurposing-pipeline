import subprocess
from pathlib import Path
from uuid import uuid4

from backend.core.config import MediaSettings, get_media_settings


class MediaConversionConfigurationError(Exception):
    pass


class MediaConversionError(Exception):
    pass


def convert_to_wav(
    input_path: Path | str,
    settings: MediaSettings | None = None,
) -> Path:
    media_settings = settings or get_media_settings()
    if not media_settings.ffmpeg_executable.strip():
        raise MediaConversionConfigurationError("FFmpeg is not configured.")

    source_path = Path(input_path)
    output_path = source_path.with_name(f"{source_path.stem}-{uuid4().hex}.wav")
    command = [
        media_settings.ffmpeg_executable,
        "-y",
        "-i",
        str(source_path),
        "-ac",
        "1",
        "-ar",
        "16000",
        "-acodec",
        "pcm_s16le",
        str(output_path),
    ]

    try:
        result = subprocess.run(
            command,
            shell=False,
            capture_output=True,
            text=True,
            timeout=media_settings.media_job_timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        _delete_if_exists(output_path)
        raise MediaConversionError("Media conversion timed out.") from exc
    except OSError as exc:
        _delete_if_exists(output_path)
        raise MediaConversionError("Media conversion failed.") from exc

    if result.returncode != 0 or not output_path.exists():
        _delete_if_exists(output_path)
        raise MediaConversionError("Media conversion failed.")

    return output_path


def _delete_if_exists(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass
