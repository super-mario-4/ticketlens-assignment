from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, update
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_session_factory
from app.main import create_app
from app.models import ImportJob, Ticket, User
from app.models.enums import Category, Priority, ReviewReason, TicketStatus, UserRole
from app.repositories.users import UserRepository
from tests.factories import build_classification, build_correction, make_ticket


def lead() -> User:
    with get_session_factory()() as own:
        repository = UserRepository(own)
        repository.add_if_missing("stats-lead", "!", UserRole.LEAD)
        own.commit()
        return repository.get_by_username("stats-lead")


@pytest.fixture
def database(migrated_database: None) -> Iterator[Session]:
    with get_session_factory()() as session:
        yield session

    with get_session_factory()() as cleanup:
        for model in (Ticket, ImportJob, User):
            cleanup.execute(delete(model))
        cleanup.commit()


@pytest.fixture
def api(database: Session) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_current_user] = lead
    return TestClient(app)


def rows(values: list[dict[str, object]]) -> dict[object, object]:
    return {row["name"]: row["count"] for row in values}


def test_empty_database_gives_zeros(api: TestClient) -> None:
    body = api.get("/api/stats").json()

    assert body["total"] == 0
    assert body["review_share"] == 0
    assert body["correction_share"] == 0
    assert body["routing_seconds_avg"] is None


def test_figures_follow_the_definitions(api: TestClient, database: Session) -> None:
    routed = make_ticket(database, status=TicketStatus.CLASSIFIED)
    database.add(build_classification(routed))
    corrected = make_ticket(database, status=TicketStatus.CLASSIFIED)
    database.add(build_classification(corrected))
    low = make_ticket(
        database, status=TicketStatus.NEEDS_REVIEW, review_reason=ReviewReason.LOW_CONFIDENCE
    )
    database.add(build_classification(low, team=None, confidence=0.4))
    make_ticket(database, status=TicketStatus.NEEDS_REVIEW, review_reason=ReviewReason.NO_CONTENT)
    make_ticket(database)
    database.execute(
        update(Ticket)
        .where(Ticket.id == routed.id)
        .values(classified_at=datetime.now(UTC) + timedelta(seconds=30))
    )
    database.commit()

    user = UserRepository(database).get_by_username("stats-lead") or lead()
    database.add(
        build_correction(
            corrected,
            user,
            old_category=Category.PAYMENTS_TRANSFERS,
            old_priority=Priority.HIGH,
            old_team="Payments",
        )
    )
    database.commit()

    body = api.get("/api/stats").json()

    assert body["total"] == 5
    assert rows(body["by_status"]) == {"classified": 2, "needs_review": 2, "pending": 1}
    assert rows(body["by_team"]) == {"Payments": 1, "Security / Fraud": 1, None: 3}
    assert rows(body["by_category"])["security_fraud"] == 1
    assert rows(body["by_category"])["payments_transfers"] == 2
    assert rows(body["by_priority"])["Critical"] == 1
    assert body["review_total"] == 2
    assert body["review_share"] == 0.4
    assert body["ai_classified"] == 3
    assert body["corrected"] == 1
    assert body["correction_share"] == pytest.approx(1 / 3)
    assert body["routing_count"] == 1
    assert 25 < body["routing_seconds_avg"] < 35


def test_a_resolved_review_ticket_still_counts_as_reviewed(
    api: TestClient, database: Session
) -> None:
    make_ticket(database, status=TicketStatus.CLASSIFIED, review_reason=ReviewReason.UNCLEAR)
    database.commit()

    assert api.get("/api/stats").json()["review_total"] == 1


def test_period_limits_the_tickets(api: TestClient, database: Session) -> None:
    make_ticket(database)
    old = make_ticket(database)
    database.execute(
        update(Ticket)
        .where(Ticket.id == old.id)
        .values(ingested_at=datetime.now(UTC) - timedelta(days=10))
    )
    database.commit()
    start = (datetime.now(UTC) - timedelta(days=1)).isoformat()

    assert api.get("/api/stats", params={"start": start}).json()["total"] == 1
    assert api.get("/api/stats", params={"end": start}).json()["total"] == 1
