import subprocess

import pytest

from backend.core.config import MediaSettings
from backend.services.media_conversion_service import MediaConversionError, convert_to_wav


def settings() -> MediaSettings:
    return MediaSettings(
        redis_url="redis://localhost:6379/0",
        rq_queue_name="media-processing",
        media_upload_dir=".data/uploads",
        media_max_upload_mb=200,
        media_job_timeout_seconds=10,
        media_job_result_ttl_seconds=60,
        media_job_failure_ttl_seconds=60,
        ffmpeg_executable="ffmpeg",
        whisper_cpp_executable="whisper",
        whisper_cpp_model_path="model.bin",
        whisper_cpp_threads=4,
    )


def test_convert_to_wav_uses_safe_ffmpeg_command(monkeypatch, tmp_path) -> None:
    source = tmp_path / "input.mp4"
    source.write_bytes(b"video")
    seen = {}

    def fake_run(command, **kwargs):
        seen["command"] = command
        seen["kwargs"] = kwargs
        output = command[-1]
        open(output, "wb").write(b"wav")
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    output = convert_to_wav(source, settings())

    assert output.suffix == ".wav"
    assert seen["kwargs"]["shell"] is False
    assert seen["command"][:4] == ["ffmpeg", "-y", "-i", str(source)]
    assert seen["command"][4:-1] == ["-ac", "1", "-ar", "16000", "-acodec", "pcm_s16le"]


def test_convert_to_wav_deletes_incomplete_output_on_failure(monkeypatch, tmp_path) -> None:
    source = tmp_path / "input.mp4"
    source.write_bytes(b"video")

    def fake_run(command, **kwargs):
        open(command[-1], "wb").write(b"incomplete")
        return subprocess.CompletedProcess(command, 1)

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(MediaConversionError):
        convert_to_wav(source, settings())

    assert list(tmp_path.glob("*.wav")) == []
