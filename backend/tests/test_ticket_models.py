from datetime import UTC, datetime, timedelta, timezone
from enum import StrEnum

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session

from app.models import Classification, Correction, ImportJob, Ticket, User
from app.models.enums import (
    Category,
    Channel,
    ImportStatus,
    Priority,
    ReviewReason,
    TicketStatus,
    UserRole,
)
from tests.factories import (
    TICKET_TIME,
    build_classification,
    build_correction,
    make_import_job,
    make_ticket,
    make_user,
)


def test_ticket_defaults(session: Session) -> None:
    ticket = make_ticket(session)
    session.refresh(ticket)

    assert ticket.id is not None
    assert ticket.status is TicketStatus.PENDING
    assert ticket.review_reason is None
    assert ticket.attempts == 0
    assert ticket.ingested_at is not None
    assert ticket.processing_started_at is None
    assert ticket.classified_at is None


def test_ticket_keeps_the_exact_moment_it_was_created(session: Session) -> None:
    tashkent_time = datetime(2026, 10, 5, 1, 10, 31, tzinfo=timezone(timedelta(hours=5)))

    ticket = make_ticket(session, created_at=tashkent_time)
    session.refresh(ticket)

    assert ticket.created_at == datetime(2026, 10, 4, 20, 10, 31, tzinfo=UTC)


def test_import_job_defaults(session: Session) -> None:
    job = make_import_job(session)
    session.refresh(job)

    assert job.status is ImportStatus.PROCESSING
    assert (job.total, job.inserted, job.skipped) == (0, 0, 0)
    assert job.errors == []
    assert job.created_at is not None


@pytest.mark.parametrize(
    ("enum_class", "type_name"),
    [
        (Channel, "ticket_channel"),
        (TicketStatus, "ticket_status"),
        (ReviewReason, "review_reason"),
        (Category, "ticket_category"),
        (Priority, "ticket_priority"),
        (ImportStatus, "import_status"),
        (UserRole, "user_role"),
    ],
)
def test_database_enums_match_the_code(
    session: Session, enum_class: type[StrEnum], type_name: str
) -> None:
    labels = session.scalars(
        text(
            "SELECT enumlabel FROM pg_enum JOIN pg_type ON pg_type.oid = enumtypid "
            "WHERE typname = :name ORDER BY enumsortorder"
        ),
        {"name": type_name},
    ).all()

    assert labels == [member.value for member in enum_class]


def test_priorities_sort_from_most_to_least_urgent(session: Session) -> None:
    ordered = session.scalars(
        text("SELECT unnest(enum_range(NULL::ticket_priority)) ORDER BY 1")
    ).all()

    assert ordered == ["Critical", "High", "Medium", "Low"]


def test_enums_are_stored_as_values(session: Session) -> None:
    make_ticket(session, channel=Channel.WEB_FORM)

    assert session.scalar(text("SELECT channel::text FROM tickets")) == "web_form"


def test_duplicate_source_ticket_id_is_rejected(session: Session) -> None:
    make_ticket(session, source_ticket_id="T-000001")

    with pytest.raises(IntegrityError, match="uq_tickets_source_ticket_id"):
        make_ticket(session, source_ticket_id="T-000001")


def test_unknown_channel_is_rejected(session: Session) -> None:
    ticket = make_ticket(session)

    with pytest.raises(DBAPIError, match="invalid input value for enum"):
        session.execute(
            text("UPDATE tickets SET channel = 'fax' WHERE id = :id"), {"id": ticket.id}
        )


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("source_ticket_id", None),
        ("channel", None),
        ("created_at", None),
        ("customer_id", None),
        ("status", None),
    ],
)
def test_required_ticket_fields(session: Session, column: str, value: None) -> None:
    ticket = make_ticket(session)

    with pytest.raises(IntegrityError, match="null value"):
        session.execute(
            text(f"UPDATE tickets SET {column} = :value WHERE id = :id"),
            {"value": value, "id": ticket.id},
        )


def test_needs_review_requires_a_reason(session: Session) -> None:
    with pytest.raises(IntegrityError, match="ck_tickets_needs_review_has_reason"):
        make_ticket(session, status=TicketStatus.NEEDS_REVIEW)


def test_review_reason_stays_after_an_operator_resolves_the_ticket(session: Session) -> None:
    ticket = make_ticket(
        session, status=TicketStatus.NEEDS_REVIEW, review_reason=ReviewReason.UNCLEAR
    )

    ticket.status = TicketStatus.CLASSIFIED
    session.flush()

    assert ticket.review_reason is ReviewReason.UNCLEAR


def test_processing_requires_a_start_time(session: Session) -> None:
    with pytest.raises(IntegrityError, match="ck_tickets_processing_has_start_time"):
        make_ticket(session, status=TicketStatus.PROCESSING)


def test_text_is_required_without_a_masking_error(session: Session) -> None:
    with pytest.raises(IntegrityError, match="ck_tickets_text_required_unless_masking_error"):
        make_ticket(session, text_masked=None)


def test_masking_error_ticket_stores_no_text(session: Session) -> None:
    ticket = make_ticket(
        session,
        text_masked=None,
        status=TicketStatus.NEEDS_REVIEW,
        review_reason=ReviewReason.MASKING_ERROR,
    )

    assert ticket.text_masked is None


def test_empty_text_is_stored_for_no_content_tickets(session: Session) -> None:
    ticket = make_ticket(
        session,
        text_masked="",
        status=TicketStatus.NEEDS_REVIEW,
        review_reason=ReviewReason.NO_CONTENT,
    )

    assert ticket.text_masked == ""


def test_attempts_cannot_be_negative(session: Session) -> None:
    with pytest.raises(IntegrityError, match="ck_tickets_attempts_non_negative"):
        make_ticket(session, attempts=-1)


@pytest.mark.parametrize("confidence", [-0.01, 1.01])
def test_confidence_must_be_between_zero_and_one(session: Session, confidence: float) -> None:
    session.add(build_classification(make_ticket(session), confidence=confidence))

    with pytest.raises(IntegrityError, match="ck_classifications_confidence_range"):
        session.flush()


@pytest.mark.parametrize("confidence", [0.0, 1.0])
def test_confidence_limits_are_allowed(session: Session, confidence: float) -> None:
    session.add(build_classification(make_ticket(session), confidence=confidence))

    session.flush()


@pytest.mark.parametrize("column", ["latency_ms", "input_tokens", "output_tokens"])
def test_usage_cannot_be_negative(session: Session, column: str) -> None:
    session.add(build_classification(make_ticket(session), **{column: -1}))

    with pytest.raises(IntegrityError, match="ck_classifications_usage_non_negative"):
        session.flush()


@pytest.mark.parametrize("column", ["total", "inserted", "skipped"])
def test_import_counts_cannot_be_negative(session: Session, column: str) -> None:
    with pytest.raises(IntegrityError, match="ck_import_jobs_counts_non_negative"):
        make_import_job(session, **{column: -1})


def test_classification_can_have_no_team(session: Session) -> None:
    session.add(build_classification(make_ticket(session), team=None))

    session.flush()


@pytest.mark.parametrize("column", ["new_category", "new_priority"])
def test_correction_requires_new_values(session: Session, column: str) -> None:
    ticket = make_ticket(session)
    session.add(build_correction(ticket, make_user(session), **{column: None}))

    with pytest.raises(IntegrityError, match="null value"):
        session.flush()


def test_correction_without_an_ai_result_has_empty_old_values(session: Session) -> None:
    correction = build_correction(make_ticket(session), make_user(session), new_team=None)
    session.add(correction)
    session.flush()

    assert correction.old_category is None
    assert correction.old_priority is None
    assert correction.old_team is None
    assert correction.new_team is None


def test_duplicate_username_is_rejected(session: Session) -> None:
    make_user(session, username="operator")

    with pytest.raises(IntegrityError, match="uq_users_username"):
        make_user(session, username="operator")


def test_classification_requires_an_existing_ticket(session: Session) -> None:
    ticket = make_ticket(session)
    classification = build_classification(ticket)
    session.delete(ticket)
    session.flush()
    session.add(classification)

    with pytest.raises(IntegrityError, match="fk_classifications_ticket_id_tickets"):
        session.flush()


def test_ticket_relationships(session: Session) -> None:
    job = make_import_job(session)
    user = make_user(session)
    ticket = make_ticket(session, import_job=job)
    first = build_classification(ticket, created_at=TICKET_TIME)
    second = build_classification(ticket, created_at=TICKET_TIME + timedelta(hours=1))
    earlier = build_correction(ticket, user, corrected_at=TICKET_TIME)
    later = build_correction(ticket, user, corrected_at=TICKET_TIME + timedelta(hours=1))
    session.add_all([second, first, later, earlier])
    session.flush()
    session.expire_all()

    loaded = session.get_one(Ticket, ticket.id)

    assert loaded.import_job.id == job.id
    assert [item.id for item in loaded.classifications] == [first.id, second.id]
    assert [item.id for item in loaded.corrections] == [earlier.id, later.id]
    assert loaded.classifications[0].ticket.id == ticket.id
    assert loaded.corrections[0].ticket.id == ticket.id
    assert loaded.corrections[0].corrector.id == user.id
    assert loaded.import_job.creator.id == job.created_by


def test_deleting_a_ticket_in_sql_removes_its_history(session: Session) -> None:
    ticket = make_ticket(session)
    session.add(build_classification(ticket))
    session.add(build_correction(ticket, make_user(session)))
    session.flush()

    session.execute(text("DELETE FROM tickets WHERE id = :id"), {"id": ticket.id})

    assert session.scalars(select(Classification)).all() == []
    assert session.scalars(select(Correction)).all() == []


def test_deleting_a_ticket_through_the_orm_removes_its_history(session: Session) -> None:
    ticket = make_ticket(session)
    session.add(build_classification(ticket))
    session.flush()
    session.expire_all()

    session.delete(session.get_one(Ticket, ticket.id))
    session.flush()

    assert session.scalars(select(Classification)).all() == []


def test_import_job_with_tickets_cannot_be_deleted(session: Session) -> None:
    ticket = make_ticket(session)

    with pytest.raises(IntegrityError, match="fk_tickets_import_job_id_import_jobs"):
        session.execute(
            text("DELETE FROM import_jobs WHERE id = :id"), {"id": ticket.import_job_id}
        )


def test_user_with_corrections_cannot_be_deleted(session: Session) -> None:
    user = make_user(session)
    session.add(build_correction(make_ticket(session), user))
    session.flush()

    with pytest.raises(IntegrityError, match="fk_corrections_corrected_by_users"):
        session.execute(text("DELETE FROM users WHERE id = :id"), {"id": user.id})


def test_user_with_import_jobs_cannot_be_deleted(session: Session) -> None:
    job = make_import_job(session)

    with pytest.raises(IntegrityError, match="fk_import_jobs_created_by_users"):
        session.execute(text("DELETE FROM users WHERE id = :id"), {"id": job.created_by})


def test_all_models_are_registered(session: Session) -> None:
    for model in (User, ImportJob, Ticket, Classification, Correction):
        assert session.scalars(select(model)).all() == []
