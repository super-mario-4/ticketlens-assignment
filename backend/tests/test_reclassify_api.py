import uuid
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.db.session import get_session_factory
from app.models import ImportJob, Ticket, User
from app.models.enums import ReviewReason, TicketStatus
from app.repositories.tickets import TicketRepository
from tests.auth import authorized_app
from tests.factories import make_ticket


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
    return TestClient(authorized_app())


def held_ticket(session: Session, reason: ReviewReason) -> Ticket:
    ticket = make_ticket(
        session,
        status=TicketStatus.NEEDS_REVIEW,
        review_reason=reason,
        text_masked=None if reason is ReviewReason.MASKING_ERROR else "Pul yo'q",
    )
    session.commit()
    return ticket


@pytest.mark.parametrize("reason", [ReviewReason.LLM_UNAVAILABLE, ReviewReason.SCHEMA_ERROR])
def test_ticket_failed_by_the_model_is_queued_again(
    api: TestClient, database: Session, reason: ReviewReason
) -> None:
    ticket = held_ticket(database, reason)

    response = api.post(f"/api/tickets/{ticket.id}/reclassify")

    assert response.status_code == 202
    assert response.json() == {"id": str(ticket.id), "status": "pending"}
    database.refresh(ticket)
    assert ticket.status is TicketStatus.PENDING
    assert ticket.review_reason is None
    claimed = TicketRepository(database).claim_pending(limit=10, now=ticket.created_at)
    assert [item.id for item in claimed] == [ticket.id]


@pytest.mark.parametrize(
    "reason",
    [
        ReviewReason.INJECTION_SUSPECTED,
        ReviewReason.NO_CONTENT,
        ReviewReason.MASKING_ERROR,
        ReviewReason.LOW_CONFIDENCE,
        ReviewReason.UNCLEAR,
    ],
)
def test_other_review_tickets_cannot_be_sent_to_the_model(
    api: TestClient, database: Session, reason: ReviewReason
) -> None:
    ticket = held_ticket(database, reason)

    response = api.post(f"/api/tickets/{ticket.id}/reclassify")

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "ticket_not_reclassifiable"
    database.refresh(ticket)
    assert ticket.status is TicketStatus.NEEDS_REVIEW
    assert ticket.review_reason is reason


@pytest.mark.parametrize("status", [TicketStatus.PENDING, TicketStatus.CLASSIFIED])
def test_ticket_outside_review_cannot_be_requeued(
    api: TestClient, database: Session, status: TicketStatus
) -> None:
    ticket = make_ticket(database, status=status)
    database.commit()

    assert api.post(f"/api/tickets/{ticket.id}/reclassify").status_code == 409


def test_a_requeued_ticket_cannot_be_requeued_twice(api: TestClient, database: Session) -> None:
    ticket = held_ticket(database, ReviewReason.LLM_UNAVAILABLE)
    api.post(f"/api/tickets/{ticket.id}/reclassify")

    assert api.post(f"/api/tickets/{ticket.id}/reclassify").status_code == 409


def test_unknown_ticket_returns_404(api: TestClient) -> None:
    response = api.post(f"/api/tickets/{uuid.uuid4()}/reclassify")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "ticket_not_found"


def test_bad_ticket_id_is_rejected(api: TestClient) -> None:
    assert api.post("/api/tickets/not-a-uuid/reclassify").status_code == 422
