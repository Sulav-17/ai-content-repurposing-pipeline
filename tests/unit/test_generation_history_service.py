from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from backend.database.base import Base
from backend.database.session import DatabaseUnavailableError
from backend.models.generation import Generation
from backend.schemas.analysis import KeywordFrequency, TranscriptAnalysis
from backend.schemas.content import ContentBrief
from backend.schemas.generation import ContentGenerationRequest, ContentGenerationResponse, PlatformContentAssets
from backend.schemas.transcript import TranscriptMetadata
from backend.services import generation_history_service
from backend.services.generation_history_service import GenerationNotFoundError


def make_session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'service.db'}")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    return SessionLocal(), engine


def generation_response() -> ContentGenerationResponse:
    return ContentGenerationResponse(
        provider="deterministic",
        project_name="Demo",
        cleaned_text="Host: Python API wins.",
        metadata=TranscriptMetadata(
            original_character_count=22,
            cleaned_character_count=22,
            word_count=4,
            line_count=1,
            changed=False,
        ),
        analysis=TranscriptAnalysis(
            sentence_count=1,
            unique_word_count=4,
            top_keywords=[KeywordFrequency(term="python", count=1)],
            key_points=["Host: Python API wins."],
        ),
        brief=ContentBrief(
            summary="Summary.",
            core_message="Message.",
            target_audience="Audience.",
            key_takeaways=["Host: Python API wins."],
            suggested_tone="Clear.",
            source_keywords=["python"],
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


def request() -> ContentGenerationRequest:
    return ContentGenerationRequest(
        text="Host: Python API wins.",
        project_name="Demo",
    )


def test_service_reuses_existing_generation_workflow(monkeypatch, tmp_path) -> None:
    called: list[dict[str, str]] = []
    session, engine = make_session(tmp_path)

    def fake_generate_content_assets(text, project_name, provider_name):
        called.append({"text": text, "project_name": project_name, "provider": provider_name})
        return generation_response()

    monkeypatch.setattr(
        generation_history_service,
        "generate_content_assets",
        fake_generate_content_assets,
    )

    response = generation_history_service.create_saved_generation(request(), session)

    assert called == [
        {
            "text": "Host: Python API wins.",
            "project_name": "Demo",
            "provider": "deterministic",
        }
    ]
    assert response.generation.assets.project_summary == "Project summary."
    session.close()
    engine.dispose()


def test_service_serializes_and_reconstructs_complete_output(monkeypatch, tmp_path) -> None:
    session, engine = make_session(tmp_path)
    monkeypatch.setattr(
        generation_history_service,
        "generate_content_assets",
        lambda *args, **kwargs: generation_response(),
    )

    saved = generation_history_service.create_saved_generation(request(), session)
    retrieved = generation_history_service.get_saved_generation(session, saved.id)

    assert retrieved.generation == generation_response()
    assert retrieved.created_at.tzinfo is not None
    session.close()
    engine.dispose()


def test_service_rolls_back_on_commit_failure(monkeypatch, tmp_path) -> None:
    session, engine = make_session(tmp_path)
    rollback_called = []
    monkeypatch.setattr(
        generation_history_service,
        "generate_content_assets",
        lambda *args, **kwargs: generation_response(),
    )
    monkeypatch.setattr(session, "commit", lambda: (_ for _ in ()).throw(SQLAlchemyError("boom")))
    monkeypatch.setattr(session, "rollback", lambda: rollback_called.append(True))

    with pytest.raises(DatabaseUnavailableError):
        generation_history_service.create_saved_generation(request(), session)

    assert rollback_called == [True]
    session.close()
    engine.dispose()


def test_service_retrieves_existing_and_handles_missing(monkeypatch, tmp_path) -> None:
    session, engine = make_session(tmp_path)
    monkeypatch.setattr(
        generation_history_service,
        "generate_content_assets",
        lambda *args, **kwargs: generation_response(),
    )
    saved = generation_history_service.create_saved_generation(request(), session)

    assert generation_history_service.get_saved_generation(session, saved.id).id == saved.id
    with pytest.raises(GenerationNotFoundError):
        generation_history_service.get_saved_generation(session, "missing")
    session.close()
    engine.dispose()


def test_service_deletes_record(monkeypatch, tmp_path) -> None:
    session, engine = make_session(tmp_path)
    monkeypatch.setattr(
        generation_history_service,
        "generate_content_assets",
        lambda *args, **kwargs: generation_response(),
    )
    saved = generation_history_service.create_saved_generation(request(), session)

    generation_history_service.delete_generation(session, saved.id)

    with pytest.raises(GenerationNotFoundError):
        generation_history_service.get_saved_generation(session, saved.id)
    session.close()
    engine.dispose()


def test_service_rolls_back_failed_delete(tmp_path, monkeypatch) -> None:
    session, engine = make_session(tmp_path)
    rollback_called = []
    record = Generation(
        id="x",
        project_name="Demo",
        provider="deterministic",
        input_text="Input",
        cleaned_text="Input",
        metadata_json=generation_response().metadata.model_dump(mode="json"),
        analysis_json=generation_response().analysis.model_dump(mode="json"),
        brief_json=generation_response().brief.model_dump(mode="json"),
        assets_json=generation_response().assets.model_dump(mode="json"),
        markdown_export="# Demo",
        created_at=datetime.now(UTC),
    )
    session.add(record)
    session.commit()
    monkeypatch.setattr(session, "commit", lambda: (_ for _ in ()).throw(SQLAlchemyError("boom")))
    monkeypatch.setattr(session, "rollback", lambda: rollback_called.append(True))

    with pytest.raises(DatabaseUnavailableError):
        generation_history_service.delete_generation(session, "x")

    assert rollback_called == [True]
    session.close()
    engine.dispose()
