from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from backend.core.config import get_settings


class DatabaseConfigurationError(Exception):
    pass


class DatabaseUnavailableError(Exception):
    pass


_engine: Engine | None = None
_sessionmaker: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        database_url = get_settings().database_url
        if not database_url:
            raise DatabaseConfigurationError("Database configuration is missing.")

        connect_args = {}
        if database_url.startswith("sqlite"):
            connect_args["check_same_thread"] = False

        _engine = create_engine(database_url, connect_args=connect_args)

    return _engine


def get_sessionmaker() -> sessionmaker[Session]:
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = sessionmaker(
            bind=get_engine(),
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )
    return _sessionmaker


def get_db_session() -> Generator[Session, None, None]:
    try:
        session = get_sessionmaker()()
    except DatabaseConfigurationError:
        raise
    except SQLAlchemyError as exc:
        raise DatabaseUnavailableError("Database is unavailable.") from exc

    try:
        yield session
    finally:
        session.close()


def reset_engine_cache() -> None:
    global _engine, _sessionmaker
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _sessionmaker = None
