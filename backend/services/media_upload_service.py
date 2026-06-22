from pathlib import Path, PurePath
from uuid import uuid4

from fastapi import UploadFile

from backend.core.config import MediaSettings, get_media_settings


class UploadValidationError(Exception):
    pass


class UploadTooLargeError(Exception):
    pass


CHUNK_SIZE = 1024 * 1024
AUDIO_SUFFIXES = {".aac", ".flac", ".m4a", ".mp3", ".ogg", ".opus", ".wav", ".wma"}
VIDEO_SUFFIXES = {".avi", ".mkv", ".mov", ".mp4", ".mpeg", ".mpg", ".webm"}
ALLOWED_SUFFIXES = AUDIO_SUFFIXES | VIDEO_SUFFIXES


async def save_upload(
    upload: UploadFile,
    settings: MediaSettings | None = None,
) -> Path:
    media_settings = settings or get_media_settings()
    suffix = _approved_suffix(upload.filename or "")
    _validate_content_type(upload.content_type, suffix)

    upload_dir = Path(media_settings.media_upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    target_path = upload_dir / f"{uuid4().hex}{suffix}"
    max_bytes = media_settings.media_max_upload_mb * 1024 * 1024
    bytes_written = 0

    try:
        with target_path.open("wb") as target_file:
            while True:
                chunk = await upload.read(CHUNK_SIZE)
                if not chunk:
                    break
                bytes_written += len(chunk)
                if bytes_written > max_bytes:
                    raise UploadTooLargeError("Uploaded file is too large.")
                target_file.write(chunk)
        if bytes_written == 0:
            raise UploadValidationError("Uploaded file is empty.")
    except Exception:
        _delete_if_exists(target_path)
        raise

    return target_path


def _approved_suffix(filename: str) -> str:
    name = PurePath(filename).name
    suffix = Path(name).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise UploadValidationError("Unsupported media file type.")
    return suffix


def _validate_content_type(content_type: str | None, suffix: str) -> None:
    if not content_type:
        return

    normalized_type = content_type.split(";", 1)[0].strip().lower()
    if normalized_type == "application/octet-stream":
        return
    if suffix in AUDIO_SUFFIXES and normalized_type.startswith("audio/"):
        return
    if suffix in VIDEO_SUFFIXES and normalized_type.startswith("video/"):
        return
    if suffix in {".m4a", ".mp4", ".webm"} and normalized_type.startswith(("audio/", "video/")):
        return

    raise UploadValidationError("Uploaded media content type does not match the file type.")


def _delete_if_exists(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass
