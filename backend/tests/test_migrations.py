from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text

from app.db.session import get_engine

TABLES = {"users", "import_jobs", "tickets", "classifications", "corrections"}
ENUM_TYPES = {
    "ticket_channel",
    "ticket_status",
    "review_reason",
    "ticket_category",
    "ticket_priority",
    "import_status",
    "user_role",
}


def existing_tables() -> set[str]:
    return set(inspect(get_engine()).get_table_names())


def existing_enum_types() -> set[str]:
    with get_engine().connect() as connection:
        return set(connection.scalars(text("SELECT typname FROM pg_type WHERE typtype = 'e'")))


@pytest.fixture
def restore_head(alembic_config: Config, migrated_database: None) -> Iterator[None]:
    yield
    command.upgrade(alembic_config, "head")


@pytest.mark.usefixtures("migrated_database")
def test_upgrade_creates_the_tables_and_types() -> None:
    assert TABLES <= existing_tables()
    assert ENUM_TYPES <= existing_enum_types()


@pytest.mark.usefixtures("migrated_database")
def test_query_paths_have_indexes() -> None:
    inspector = inspect(get_engine())

    def indexed_columns(table: str) -> list[list[str | None]]:
        return [index["column_names"] for index in inspector.get_indexes(table)]

    assert indexed_columns("tickets") == [
        ["channel", "created_at"],
        ["import_job_id"],
        ["ingested_at"],
        ["status", "created_at"],
        ["source_ticket_id"],
    ]
    assert indexed_columns("classifications") == [["ticket_id", "created_at"]]
    assert indexed_columns("corrections") == [["ticket_id", "corrected_at"]]


@pytest.mark.usefixtures("restore_head")
def test_downgrade_removes_everything_and_upgrade_restores_it(alembic_config: Config) -> None:
    command.downgrade(alembic_config, "0001")

    assert existing_tables() == {"alembic_version"}
    assert existing_enum_types() == set()

    command.upgrade(alembic_config, "head")

    assert TABLES <= existing_tables()
    assert ENUM_TYPES <= existing_enum_types()
