import json
import subprocess

import pytest

from backend.core.config import MediaSettings
from backend.transcription.base import TranscriptionConfigurationError, TranscriptionError
from backend.transcription.whisper_cpp import WhisperCppTranscriber


def settings(executable: str, model: str) -> MediaSettings:
    return MediaSettings(
        redis_url="redis://localhost:6379/0",
        rq_queue_name="media-processing",
        media_upload_dir=".data/uploads",
        media_max_upload_mb=200,
        media_job_timeout_seconds=10,
        media_job_result_ttl_seconds=60,
        media_job_failure_ttl_seconds=60,
        ffmpeg_executable="ffmpeg",
        whisper_cpp_executable=executable,
        whisper_cpp_model_path=model,
        whisper_cpp_threads=4,
    )


def make_files(tmp_path):
    executable = tmp_path / "whisper-cli.exe"
    model = tmp_path / "model.bin"
    wav = tmp_path / "audio.wav"
    executable.write_bytes(b"exe")
    model.write_bytes(b"model")
    wav.write_bytes(b"wav")
    return executable, model, wav


def test_transcriber_invokes_whisper_json_output_and_parses_segments(monkeypatch, tmp_path) -> None:
    executable, model, wav = make_files(tmp_path)
    seen = {}

    def fake_run(command, **kwargs):
        seen["command"] = command
        seen["kwargs"] = kwargs
        prefix = command[command.index("--output-file") + 1]
        with open(f"{prefix}.json", "w", encoding="utf-8") as output:
            json.dump(
                {
                    "transcription": [
                        {
                            "timestamps": {"from": "00:00:05,000", "to": "00:00:08,000"},
                            "text": " Hello world. ",
                        }
                    ]
                },
                output,
            )
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = WhisperCppTranscriber(settings(str(executable), str(model))).transcribe(wav, language="en")

    assert result.text == "[00:05] Hello world."
    assert result.segments[0].start_seconds == 5
    assert "--output-json-full" in seen["command"]
    assert "--output-file" in seen["command"]
    assert seen["kwargs"]["shell"] is False
    assert list(tmp_path.glob("*whisper*.json")) == []


def test_transcriber_validates_configuration(tmp_path) -> None:
    with pytest.raises(TranscriptionConfigurationError):
        WhisperCppTranscriber(settings(str(tmp_path / "missing.exe"), str(tmp_path / "missing.bin"))).transcribe(
            tmp_path / "audio.wav"
        )


@pytest.mark.parametrize(
    "payload",
    [
        b"\xff\xfe",
        b"{not json",
        json.dumps({"missing": []}).encode("utf-8"),
        json.dumps({"transcription": [{"timestamps": {"from": "bad", "to": "00:01"}, "text": "Hi"}]}).encode("utf-8"),
        json.dumps({"transcription": [{"timestamps": {"from": "00:00", "to": "00:01"}, "text": "   "}]}).encode("utf-8"),
    ],
)
def test_transcriber_rejects_malformed_or_blank_output(monkeypatch, tmp_path, payload) -> None:
    executable, model, wav = make_files(tmp_path)

    def fake_run(command, **kwargs):
        prefix = command[command.index("--output-file") + 1]
        with open(f"{prefix}.json", "wb") as output:
            output.write(payload)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(TranscriptionError):
        WhisperCppTranscriber(settings(str(executable), str(model))).transcribe(wav)
