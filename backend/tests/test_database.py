import pytest
from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import text

from app.core.config import Settings
from app.db.base import Base
from app.db.session import get_db, get_engine


def test_database_url_uses_the_psycopg_driver_and_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("POSTGRES_HOST", "db.example")
    monkeypatch.setenv("POSTGRES_PORT", "6543")
    monkeypatch.setenv("POSTGRES_USER", "app")
    monkeypatch.setenv("POSTGRES_PASSWORD", "p@ss/word")
    monkeypatch.setenv("POSTGRES_DB", "tickets")

    url = Settings().database_url

    assert url.drivername == "postgresql+psycopg"
    assert (url.host, url.port, url.username, url.database) == (
        "db.example",
        6543,
        "app",
        "tickets",
    )
    assert url.password == "p@ss/word"


def test_password_is_hidden_when_settings_are_printed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("POSTGRES_PASSWORD", "very-secret-value")

    assert "very-secret-value" not in repr(Settings())


def test_metadata_uses_the_naming_convention() -> None:
    assert Base.metadata.naming_convention["pk"] == "pk_%(table_name)s"


@pytest.mark.usefixtures("migrated_database")
def test_engine_connects_to_postgres() -> None:
    with get_engine().connect() as connection:
        assert connection.execute(text("SELECT 1")).scalar_one() == 1


@pytest.mark.usefixtures("migrated_database")
def test_session_dependency_provides_a_working_session() -> None:
    session_generator = get_db()
    session = next(session_generator)

    assert session.execute(text("SELECT 1")).scalar_one() == 1
    session_generator.close()


@pytest.mark.usefixtures("migrated_database")
def test_migrations_reach_head(alembic_config: Config) -> None:
    head = ScriptDirectory.from_config(alembic_config).get_current_head()

    with get_engine().connect() as connection:
        current = MigrationContext.configure(connection).get_current_revision()

    assert current == head


@pytest.mark.usefixtures("migrated_database")
def test_models_and_migrations_are_in_sync(alembic_config: Config) -> None:
    command.check(alembic_config)
