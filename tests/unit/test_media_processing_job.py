from backend.jobs import media_processing
from backend.schemas.analysis import KeywordFrequency, TranscriptAnalysis
from backend.schemas.content import ContentBrief
from backend.schemas.generation import ContentGenerationResponse, PlatformContentAssets
from backend.schemas.media_jobs import TranscriptionResult, TranscriptionSegment
from backend.schemas.transcript import TranscriptMetadata


class FakeJob:
    def __init__(self) -> None:
        self.meta = {}
        self.saved_meta = 0

    def save_meta(self):
        self.saved_meta += 1


def generation_response() -> ContentGenerationResponse:
    return ContentGenerationResponse(
        provider="deterministic",
        project_name="Demo",
        cleaned_text="[00:05] Hello world.",
        metadata=TranscriptMetadata(
            original_character_count=19,
            cleaned_character_count=19,
            word_count=3,
            line_count=1,
            changed=False,
        ),
        analysis=TranscriptAnalysis(
            sentence_count=1,
            unique_word_count=2,
            top_keywords=[KeywordFrequency(term="hello", count=1)],
            key_points=["[00:05] Hello world."],
        ),
        brief=ContentBrief(
            summary="Summary.",
            core_message="Message.",
            target_audience="Audience.",
            key_takeaways=["Hello world."],
            suggested_tone="Clear.",
            source_keywords=["hello"],
        ),
        assets=PlatformContentAssets(
            youtube_titles=["Title 1", "Title 2", "Title 3", "Title 4", "Title 5"],
            youtube_description="Description.",
            youtube_chapters=[],
            linkedin_post="Post.",
            short_hooks=["Hook 1", "Hook 2", "Hook 3", "Hook 4", "Hook 5"],
            short_form_concepts=["Concept 1", "Concept 2", "Concept 3"],
            portfolio_notes=["Note 1", "Note 2", "Note 3"],
            project_summary="Project summary.",
        ),
        markdown_export="# Demo",
    )


def transcription_result() -> TranscriptionResult:
    return TranscriptionResult(
        text="[00:05] Hello world.",
        segments=[TranscriptionSegment(start_seconds=5, end_seconds=8, text="Hello world.")],
        language="en",
    )


def test_worker_updates_stages_reuses_generation_and_saves_without_duplicate(monkeypatch, tmp_path) -> None:
    upload_path = tmp_path / "upload.mp4"
    wav_path = tmp_path / "converted.wav"
    upload_path.write_bytes(b"upload")
    wav_path.write_bytes(b"wav")
    job = FakeJob()
    calls = []

    class FakeTranscriber:
        def transcribe(self, path, language=None):
            calls.append(("transcribe", str(path), language))
            return transcription_result()

    class FakeSession:
        def close(self):
            calls.append(("close",))

    monkeypatch.setattr(media_processing, "get_current_job", lambda: job)
    monkeypatch.setattr(media_processing, "convert_to_wav", lambda path: wav_path)
    monkeypatch.setattr(media_processing, "WhisperCppTranscriber", lambda: FakeTranscriber())
    monkeypatch.setattr(media_processing, "generate_content_assets", lambda **kwargs: generation_response())
    monkeypatch.setattr(media_processing, "get_sessionmaker", lambda: lambda: FakeSession())
    monkeypatch.setattr(
        media_processing,
        "persist_generated_response",
        lambda session, request, generation_response: type("Saved", (), {"id": "saved-1"})(),
    )

    result = media_processing.process_media_job(str(upload_path), "Demo", "deterministic", True, "en")

    assert result["status"] == "finished"
    assert result["saved_generation_id"] == "saved-1"
    assert job.meta["stage"] == "complete"
    assert job.saved_meta >= 5
    assert ("transcribe", str(wav_path), "en") in calls
    assert ("close",) in calls
    assert not upload_path.exists()
    assert not wav_path.exists()


def test_worker_save_false_does_not_require_database(monkeypatch, tmp_path) -> None:
    upload_path = tmp_path / "upload.mp4"
    wav_path = tmp_path / "converted.wav"
    upload_path.write_bytes(b"upload")
    wav_path.write_bytes(b"wav")

    class FakeTranscriber:
        def transcribe(self, path, language=None):
            return transcription_result()

    monkeypatch.setattr(media_processing, "get_current_job", lambda: FakeJob())
    monkeypatch.setattr(media_processing, "convert_to_wav", lambda path: wav_path)
    monkeypatch.setattr(media_processing, "WhisperCppTranscriber", lambda: FakeTranscriber())
    monkeypatch.setattr(media_processing, "generate_content_assets", lambda **kwargs: generation_response())
    monkeypatch.setattr(media_processing, "get_sessionmaker", lambda: (_ for _ in ()).throw(AssertionError("db used")))

    result = media_processing.process_media_job(str(upload_path), "Demo", "deterministic", False, None)

    assert result["status"] == "finished"
    assert result["saved_generation_id"] is None


def test_worker_returns_safe_failure_and_cleans_files(monkeypatch, tmp_path) -> None:
    upload_path = tmp_path / "upload.mp4"
    upload_path.write_bytes(b"upload")
    job = FakeJob()
    monkeypatch.setattr(media_processing, "get_current_job", lambda: job)
    monkeypatch.setattr(media_processing, "convert_to_wav", lambda path: (_ for _ in ()).throw(RuntimeError("secret")))

    result = media_processing.process_media_job(str(upload_path), "Demo", "deterministic", False, None)

    assert result["status"] == "failed"
    assert result["error"] == "Media processing failed."
    assert "secret" not in result["error"]
    assert job.meta["stage"] == "failed"
    assert not upload_path.exists()
