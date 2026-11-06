import uuid
from collections.abc import Iterator
from datetime import timedelta

import pytest
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.session import get_session_factory
from app.models import Classification, Correction, ImportJob, Ticket, User
from app.models.enums import Category, Channel, Priority, ReviewReason, TicketStatus
from app.repositories.tickets import TicketFilters, TicketPage, TicketRepository
from tests.factories import (
    TICKET_TIME,
    build_classification,
    build_correction,
    make_import_job,
    make_ticket,
    make_user,
)


@pytest.fixture
def repository(session: Session) -> TicketRepository:
    return TicketRepository(session)


def classify(session: Session, priority: Priority, **ticket_values: object) -> Ticket:
    ticket = make_ticket(session, status=TicketStatus.CLASSIFIED, **ticket_values)
    session.add(build_classification(ticket, priority=priority))
    session.flush()
    return ticket


def ids(page: TicketPage) -> list[uuid.UUID]:
    return [item.ticket.id for item in page.items]


def add_if_new(repository: TicketRepository, job: ImportJob, **overrides: object) -> uuid.UUID:
    values = {
        "source_ticket_id": "T-000001",
        "channel": Channel.EMAIL,
        "created_at": TICKET_TIME,
        "customer_id": "C576052",
        "text_masked": "Salom",
        "import_job_id": job.id,
    }
    return repository.add_if_new(**values | overrides)


def test_add_if_new_creates_a_pending_ticket(
    session: Session, repository: TicketRepository
) -> None:
    ticket_id = add_if_new(repository, make_import_job(session))

    ticket = session.get_one(Ticket, ticket_id)
    assert ticket.source_ticket_id == "T-000001"
    assert ticket.status is TicketStatus.PENDING


def test_add_if_new_skips_a_source_id_already_imported(
    session: Session, repository: TicketRepository
) -> None:
    job = make_import_job(session)
    first = add_if_new(repository, job, customer_id="C111111")

    second = add_if_new(repository, make_import_job(session), customer_id="C222222")

    assert second is None
    assert session.get_one(Ticket, first).customer_id == "C111111"
    assert len(session.scalars(select(Ticket)).all()) == 1


def test_add_if_new_stores_a_review_ticket(session: Session, repository: TicketRepository) -> None:
    ticket_id = add_if_new(
        repository,
        make_import_job(session),
        text_masked="",
        status=TicketStatus.NEEDS_REVIEW,
        review_reason=ReviewReason.NO_CONTENT,
    )

    ticket = session.get_one(Ticket, ticket_id)
    assert ticket.status is TicketStatus.NEEDS_REVIEW
    assert ticket.review_reason is ReviewReason.NO_CONTENT


def test_get_returns_none_for_an_unknown_ticket(repository: TicketRepository) -> None:
    assert repository.get(uuid.uuid4()) is None


def test_get_loads_the_ticket_history(session: Session, repository: TicketRepository) -> None:
    ticket = make_ticket(session)
    repository.add_classification(build_classification(ticket))
    repository.add_correction(build_correction(ticket, make_user(session)))
    session.expire_all()

    view = repository.get(ticket.id)

    assert view is not None
    assert len(view.ticket.classifications) == 1
    assert len(view.ticket.corrections) == 1


def test_ticket_without_results_has_no_effective_values(
    session: Session, repository: TicketRepository
) -> None:
    view = repository.get(make_ticket(session).id)

    assert view is not None
    assert (view.category, view.priority, view.team) == (None, None, None)


def test_effective_values_come_from_the_latest_classification(
    session: Session, repository: TicketRepository
) -> None:
    ticket = make_ticket(session)
    repository.add_classification(
        build_classification(ticket, category=Category.REFUNDS, created_at=TICKET_TIME)
    )
    repository.add_classification(
        build_classification(
            ticket,
            category=Category.CARD_ISSUES,
            priority=Priority.MEDIUM,
            team="Cards",
            created_at=TICKET_TIME + timedelta(hours=1),
        )
    )

    view = repository.get(ticket.id)

    assert view is not None
    assert (view.category, view.priority, view.team) == (
        Category.CARD_ISSUES,
        Priority.MEDIUM,
        "Cards",
    )


def test_a_correction_overrides_the_classification(
    session: Session, repository: TicketRepository
) -> None:
    ticket = make_ticket(session)
    repository.add_classification(
        build_classification(ticket, created_at=TICKET_TIME + timedelta(days=1))
    )
    repository.add_correction(
        build_correction(ticket, make_user(session), corrected_at=TICKET_TIME)
    )

    view = repository.get(ticket.id)

    assert view is not None
    assert (view.category, view.priority, view.team) == (
        Category.SECURITY_FRAUD,
        Priority.CRITICAL,
        "Security / Fraud",
    )


def test_the_latest_correction_wins_and_history_is_kept(
    session: Session, repository: TicketRepository
) -> None:
    ticket = make_ticket(session)
    user = make_user(session)
    repository.add_correction(
        build_correction(ticket, user, new_category=Category.REFUNDS, corrected_at=TICKET_TIME)
    )
    repository.add_correction(
        build_correction(
            ticket,
            user,
            new_category=Category.CARD_ISSUES,
            corrected_at=TICKET_TIME + timedelta(hours=1),
        )
    )

    view = repository.get(ticket.id)

    assert view is not None
    assert view.category is Category.CARD_ISSUES
    assert len(view.ticket.corrections) == 2


def test_a_correction_that_clears_the_team_does_not_bring_back_the_ai_team(
    session: Session, repository: TicketRepository
) -> None:
    ticket = make_ticket(session)
    repository.add_classification(build_classification(ticket, team="Payments"))
    repository.add_correction(
        build_correction(ticket, make_user(session), new_category=Category.OTHER, new_team=None)
    )

    view = repository.get(ticket.id)

    assert view is not None
    assert view.team is None


def test_queue_orders_by_priority_then_oldest_first(
    session: Session, repository: TicketRepository
) -> None:
    newer_critical = classify(
        session, Priority.CRITICAL, created_at=TICKET_TIME + timedelta(hours=1)
    )
    older_critical = classify(session, Priority.CRITICAL, created_at=TICKET_TIME)
    low = classify(session, Priority.LOW, created_at=TICKET_TIME - timedelta(days=1))
    high = classify(session, Priority.HIGH)
    medium = classify(session, Priority.MEDIUM)
    unclassified = make_ticket(session, created_at=TICKET_TIME - timedelta(days=2))

    page = repository.list_tickets(TicketFilters(), limit=10, offset=0)

    assert ids(page) == [
        older_critical.id,
        newer_critical.id,
        high.id,
        medium.id,
        low.id,
        unclassified.id,
    ]


def test_queue_order_uses_the_corrected_priority(
    session: Session, repository: TicketRepository
) -> None:
    high = classify(session, Priority.HIGH)
    low = classify(session, Priority.LOW)
    repository.add_correction(
        build_correction(low, make_user(session), new_priority=Priority.CRITICAL)
    )

    page = repository.list_tickets(TicketFilters(), limit=10, offset=0)

    assert ids(page) == [low.id, high.id]


def test_queue_leaves_out_tickets_in_manual_review(
    session: Session, repository: TicketRepository
) -> None:
    classified = classify(session, Priority.LOW)
    make_ticket(session, status=TicketStatus.NEEDS_REVIEW, review_reason=ReviewReason.UNCLEAR)

    page = repository.list_tickets(TicketFilters(), limit=10, offset=0)

    assert ids(page) == [classified.id]
    assert page.total == 1


def test_review_list_is_oldest_first_regardless_of_priority(
    session: Session, repository: TicketRepository
) -> None:
    def review_ticket(created_at_offset: int, priority: Priority) -> Ticket:
        ticket = make_ticket(
            session,
            status=TicketStatus.NEEDS_REVIEW,
            review_reason=ReviewReason.LOW_CONFIDENCE,
            created_at=TICKET_TIME + timedelta(hours=created_at_offset),
        )
        repository.add_classification(build_classification(ticket, priority=priority))
        return ticket

    newer_critical = review_ticket(1, Priority.CRITICAL)
    older_low = review_ticket(0, Priority.LOW)

    page = repository.list_tickets(
        TicketFilters(status=TicketStatus.NEEDS_REVIEW), limit=10, offset=0
    )

    assert ids(page) == [older_low.id, newer_critical.id]


@pytest.mark.parametrize(
    "filters",
    [
        TicketFilters(category=Category.REFUNDS),
        TicketFilters(priority=Priority.LOW),
        TicketFilters(team="Refunds"),
        TicketFilters(channel=Channel.EMAIL),
        TicketFilters(status=TicketStatus.CLASSIFIED),
        TicketFilters(
            category=Category.REFUNDS,
            priority=Priority.LOW,
            team="Refunds",
            channel=Channel.EMAIL,
            status=TicketStatus.CLASSIFIED,
        ),
    ],
)
def test_filters_select_matching_tickets(
    session: Session, repository: TicketRepository, filters: TicketFilters
) -> None:
    match = make_ticket(session, channel=Channel.EMAIL, status=TicketStatus.CLASSIFIED)
    repository.add_classification(
        build_classification(
            match, category=Category.REFUNDS, priority=Priority.LOW, team="Refunds"
        )
    )
    other = make_ticket(session, channel=Channel.TELEGRAM)
    repository.add_classification(build_classification(other))

    page = repository.list_tickets(filters, limit=10, offset=0)

    assert ids(page) == [match.id]
    assert page.total == 1


def test_filters_use_corrected_values(session: Session, repository: TicketRepository) -> None:
    ticket = classify(session, Priority.LOW)
    repository.add_correction(build_correction(ticket, make_user(session)))

    corrected = repository.list_tickets(
        TicketFilters(category=Category.SECURITY_FRAUD), limit=10, offset=0
    )
    original = repository.list_tickets(
        TicketFilters(category=Category.PAYMENTS_TRANSFERS), limit=10, offset=0
    )

    assert ids(corrected) == [ticket.id]
    assert ids(original) == []


def test_pagination_returns_a_page_and_the_full_total(
    session: Session, repository: TicketRepository
) -> None:
    tickets = [
        classify(session, Priority.HIGH, created_at=TICKET_TIME + timedelta(hours=hour))
        for hour in range(5)
    ]

    page = repository.list_tickets(TicketFilters(), limit=2, offset=2)

    assert ids(page) == [tickets[2].id, tickets[3].id]
    assert page.total == 5


def test_tickets_with_several_results_appear_once(
    session: Session, repository: TicketRepository
) -> None:
    ticket = classify(session, Priority.HIGH)
    repository.add_classification(build_classification(ticket))
    user = make_user(session)
    repository.add_correction(build_correction(ticket, user))
    repository.add_correction(build_correction(ticket, user))

    page = repository.list_tickets(TicketFilters(), limit=10, offset=0)

    assert ids(page) == [ticket.id]
    assert page.total == 1


def test_claim_pending_takes_the_oldest_tickets(
    session: Session, repository: TicketRepository
) -> None:
    now = TICKET_TIME + timedelta(days=1)
    newest = make_ticket(session, created_at=TICKET_TIME + timedelta(hours=2))
    oldest = make_ticket(session, created_at=TICKET_TIME)
    middle = make_ticket(session, created_at=TICKET_TIME + timedelta(hours=1))

    claimed = repository.claim_pending(limit=2, now=now)

    assert [ticket.id for ticket in claimed] == [oldest.id, middle.id]
    assert all(ticket.status is TicketStatus.PROCESSING for ticket in claimed)
    assert all(ticket.processing_started_at == now for ticket in claimed)
    assert all(ticket.attempts == 1 for ticket in claimed)
    session.refresh(newest)
    assert newest.status is TicketStatus.PENDING


def test_claim_pending_ignores_other_statuses(
    session: Session, repository: TicketRepository
) -> None:
    make_ticket(session, status=TicketStatus.CLASSIFIED)
    make_ticket(session, status=TicketStatus.NEEDS_REVIEW, review_reason=ReviewReason.NO_CONTENT)

    assert repository.claim_pending(limit=10, now=TICKET_TIME) == []


@pytest.fixture
def committed_tickets() -> Iterator[None]:
    """Two pending tickets that other connections can see."""
    with get_session_factory()() as setup:
        job = make_import_job(setup)
        make_ticket(setup, import_job=job)
        make_ticket(setup, import_job=job)
        setup.commit()

    yield

    with get_session_factory()() as cleanup:
        for model in (Ticket, ImportJob, User):
            cleanup.execute(delete(model))
        cleanup.commit()


@pytest.mark.usefixtures("migrated_database", "committed_tickets")
def test_two_workers_never_claim_the_same_ticket() -> None:
    factory = get_session_factory()
    with factory() as first_worker, factory() as second_worker:
        first = TicketRepository(first_worker).claim_pending(limit=1, now=TICKET_TIME)
        second = TicketRepository(second_worker).claim_pending(limit=2, now=TICKET_TIME)

        assert len(first) == 1
        assert len(second) == 1
        assert first[0].id != second[0].id


def test_requeue_stale_returns_abandoned_tickets_to_pending(
    session: Session, repository: TicketRepository
) -> None:
    cutoff = TICKET_TIME
    stale = make_ticket(
        session,
        status=TicketStatus.PROCESSING,
        processing_started_at=cutoff - timedelta(minutes=1),
    )
    active = make_ticket(
        session,
        status=TicketStatus.PROCESSING,
        processing_started_at=cutoff + timedelta(minutes=1),
    )

    assert repository.requeue_stale(started_before=cutoff) == 1

    session.expire_all()
    assert stale.status is TicketStatus.PENDING
    assert stale.processing_started_at is None
    assert active.status is TicketStatus.PROCESSING


def test_delete_ingested_before_removes_expired_tickets_and_history(
    session: Session, repository: TicketRepository
) -> None:
    cutoff = TICKET_TIME
    expired = make_ticket(session, ingested_at=cutoff - timedelta(seconds=1))
    repository.add_classification(build_classification(expired))
    repository.add_correction(build_correction(expired, make_user(session)))
    kept = make_ticket(session, ingested_at=cutoff)
    repository.add_classification(build_classification(kept))

    deleted = repository.delete_ingested_before(cutoff)

    session.expire_all()
    assert deleted == [expired.id]
    assert repository.get(kept.id) is not None
    assert session.scalars(select(Classification.ticket_id)).all() == [kept.id]
    assert session.scalars(select(Correction)).all() == []


def test_repository_does_not_commit(session: Session, repository: TicketRepository) -> None:
    ticket_id = add_if_new(repository, make_import_job(session))

    session.rollback()

    assert session.get(Ticket, ticket_id) is None
