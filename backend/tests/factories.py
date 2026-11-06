import itertools
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models import Classification, Correction, ImportJob, Ticket, User
from app.models.enums import Category, Channel, Priority, UserRole

_sequence = itertools.count(1)

TICKET_TIME = datetime(2026, 10, 5, 12, 0, tzinfo=UTC)


def make_user(session: Session, **overrides: Any) -> User:
    number = next(_sequence)
    values = {"username": f"user-{number}", "password_hash": "hash", "role": UserRole.OPERATOR}
    user = User(**values | overrides)
    session.add(user)
    session.flush()
    return user


def make_import_job(session: Session, **overrides: Any) -> ImportJob:
    values = {"filename": "tickets.csv", "creator": make_user(session)}
    job = ImportJob(**values | overrides)
    session.add(job)
    session.flush()
    return job


def make_ticket(session: Session, **overrides: Any) -> Ticket:
    number = next(_sequence)
    values = {
        "source_ticket_id": f"T-{number:06d}",
        "channel": Channel.TELEGRAM,
        "created_at": TICKET_TIME,
        "customer_id": "C576052",
        "text_masked": "Pulim yetib bormadi",
    }
    if "import_job" not in overrides and "import_job_id" not in overrides:
        values["import_job"] = make_import_job(session)
    ticket = Ticket(**values | overrides)
    session.add(ticket)
    session.flush()
    return ticket


def build_classification(ticket: Ticket, **overrides: Any) -> Classification:
    values = {
        "ticket_id": ticket.id,
        "model": "qwen3.6:35b-a3b",
        "prompt_version": "v1",
        "category": Category.PAYMENTS_TRANSFERS,
        "priority": Priority.HIGH,
        "confidence": 0.86,
        "summary": "Mijoz o'tkazma yetib bormaganini yozgan.",
        "team": "Payments",
        "latency_ms": 1200,
        "input_tokens": 950,
        "output_tokens": 110,
    }
    return Classification(**values | overrides)


def build_correction(ticket: Ticket, user: User, **overrides: Any) -> Correction:
    values = {
        "ticket_id": ticket.id,
        "new_category": Category.SECURITY_FRAUD,
        "new_priority": Priority.CRITICAL,
        "new_team": "Security / Fraud",
        "corrected_by": user.id,
    }
    return Correction(**values | overrides)
