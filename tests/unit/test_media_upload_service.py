import asyncio
from pathlib import Path

import pytest

from backend.core.config import MediaSettings
from backend.services.media_upload_service import (
    UploadTooLargeError,
    UploadValidationError,
    save_upload,
)


class FakeUpload:
    def __init__(self, filename: str, content_type: str, chunks: list[bytes]) -> None:
        self.filename = filename
        self.content_type = content_type
        self._chunks = list(chunks)

    async def read(self, size: int) -> bytes:
        if not self._chunks:
            return b""
        return self._chunks.pop(0)


def settings(tmp_path, max_mb: int = 1) -> MediaSettings:
    return MediaSettings(
        redis_url="redis://localhost:6379/0",
        rq_queue_name="media-processing",
        media_upload_dir=str(tmp_path),
        media_max_upload_mb=max_mb,
        media_job_timeout_seconds=60,
        media_job_result_ttl_seconds=60,
        media_job_failure_ttl_seconds=60,
        ffmpeg_executable="ffmpeg",
        whisper_cpp_executable="whisper",
        whisper_cpp_model_path="model.bin",
        whisper_cpp_threads=4,
    )


def test_save_upload_streams_chunks_and_uses_uuid_filename(tmp_path) -> None:
    upload = FakeUpload("../Unsafe Name.MP3", "application/octet-stream", [b"abc", b"def"])

    path = asyncio.run(save_upload(upload, settings(tmp_path)))

    assert path.parent == tmp_path
    assert path.suffix == ".mp3"
    assert path.name != "Unsafe Name.MP3"
    assert path.read_bytes() == b"abcdef"


def test_save_upload_rejects_invalid_extension_and_content_type(tmp_path) -> None:
    with pytest.raises(UploadValidationError):
        asyncio.run(save_upload(FakeUpload("clip.exe", "application/octet-stream", [b"x"]), settings(tmp_path)))

    with pytest.raises(UploadValidationError):
        asyncio.run(save_upload(FakeUpload("clip.mp3", "image/png", [b"x"]), settings(tmp_path)))


def test_save_upload_rejects_empty_and_oversized_files_and_cleans_partial(tmp_path) -> None:
    with pytest.raises(UploadValidationError):
        asyncio.run(save_upload(FakeUpload("empty.wav", "audio/wav", []), settings(tmp_path)))

    with pytest.raises(UploadTooLargeError):
        asyncio.run(
            save_upload(
                FakeUpload("large.wav", "audio/wav", [b"a" * 1024 * 1024, b"b"]),
                settings(tmp_path, max_mb=1),
            )
        )

    assert list(tmp_path.iterdir()) == []
