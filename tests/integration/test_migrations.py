from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def test_initial_migration_upgrades_and_downgrades_sqlite_database(tmp_path) -> None:
    database_path = tmp_path / "migration.db"
    database_url = f"sqlite:///{database_path}"
    alembic_config = Config("alembic.ini")
    alembic_config.set_main_option("sqlalchemy.url", database_url)

    command.upgrade(alembic_config, "head")
    engine = create_engine(database_url)
    inspector = inspect(engine)
    assert "generations" in inspector.get_table_names()
    engine.dispose()

    command.downgrade(alembic_config, "base")
    engine = create_engine(database_url)
    inspector = inspect(engine)
    assert "generations" not in inspector.get_table_names()
    engine.dispose()
