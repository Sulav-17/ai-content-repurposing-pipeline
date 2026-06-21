from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database.base import Base
from backend.models.generation import Generation
from backend.repositories.generation_repository import GenerationRepository


def make_session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'repository.db'}")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    return SessionLocal(), engine


def make_record(record_id: str, created_at: datetime) -> Generation:
    return Generation(
        id=record_id,
        project_name=f"Project {record_id}",
        provider="deterministic",
        input_text="Host: Python API wins.",
        cleaned_text="Host: Python API wins.",
        metadata_json={
            "original_character_count": 22,
            "cleaned_character_count": 22,
            "word_count": 4,
            "line_count": 1,
            "changed": False,
        },
        analysis_json={
            "sentence_count": 1,
            "unique_word_count": 4,
            "top_keywords": [{"term": "python", "count": 1}],
            "key_points": ["Host: Python API wins."],
        },
        brief_json={
            "summary": "Summary.",
            "core_message": "Message.",
            "target_audience": "Audience.",
            "key_takeaways": ["Host: Python API wins."],
            "suggested_tone": "Clear.",
            "source_keywords": ["python"],
        },
        assets_json={
            "youtube_titles": ["Title 1", "Title 2", "Title 3", "Title 4", "Title 5"],
            "youtube_description": "Description.",
            "youtube_chapters": [],
            "linkedin_post": "Post.",
            "short_hooks": ["Hook 1", "Hook 2", "Hook 3", "Hook 4", "Hook 5"],
            "short_form_concepts": ["Concept 1", "Concept 2", "Concept 3"],
            "portfolio_notes": ["Note 1", "Note 2", "Note 3"],
            "project_summary": f"Summary {record_id}.",
        },
        markdown_export="# Project",
        created_at=created_at,
    )


def test_repository_creates_and_gets_record(tmp_path) -> None:
    session, engine = make_session(tmp_path)
    repository = GenerationRepository(session)
    record = make_record("b", datetime.now(UTC))

    repository.create(record)
    session.commit()

    assert repository.get_by_id("b") == record
    session.close()
    engine.dispose()


def test_repository_returns_none_for_missing_record(tmp_path) -> None:
    session, engine = make_session(tmp_path)

    assert GenerationRepository(session).get_by_id("missing") is None
    session.close()
    engine.dispose()


def test_repository_lists_newest_first_with_id_tie_breaker(tmp_path) -> None:
    session, engine = make_session(tmp_path)
    repository = GenerationRepository(session)
    now = datetime.now(UTC)
    repository.create(make_record("a", now - timedelta(minutes=1)))
    repository.create(make_record("b", now))
    repository.create(make_record("c", now))
    session.commit()

    records = repository.list(limit=10, offset=0)

    assert [record.id for record in records] == ["c", "b", "a"]
    session.close()
    engine.dispose()


def test_repository_supports_limit_and_offset(tmp_path) -> None:
    session, engine = make_session(tmp_path)
    repository = GenerationRepository(session)
    now = datetime.now(UTC)
    for index, record_id in enumerate(["a", "b", "c"]):
        repository.create(make_record(record_id, now + timedelta(minutes=index)))
    session.commit()

    records = repository.list(limit=1, offset=1)

    assert len(records) == 1
    assert records[0].id == "b"
    session.close()
    engine.dispose()


def test_repository_counts_records(tmp_path) -> None:
    session, engine = make_session(tmp_path)
    repository = GenerationRepository(session)
    repository.create(make_record("a", datetime.now(UTC)))
    repository.create(make_record("b", datetime.now(UTC)))
    session.commit()

    assert repository.count() == 2
    session.close()
    engine.dispose()


def test_repository_deletes_record(tmp_path) -> None:
    session, engine = make_session(tmp_path)
    repository = GenerationRepository(session)
    record = make_record("a", datetime.now(UTC))
    repository.create(record)
    session.commit()

    repository.delete(record)
    session.commit()

    assert repository.get_by_id("a") is None
    session.close()
    engine.dispose()


def test_repository_delete_missing_is_not_called_for_none(tmp_path) -> None:
    session, engine = make_session(tmp_path)
    repository = GenerationRepository(session)

    assert repository.get_by_id("missing") is None
    session.close()
    engine.dispose()
