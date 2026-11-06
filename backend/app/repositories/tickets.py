import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import ColumnElement, Select, case, delete, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session, selectinload

from app.models import Classification, Correction, Ticket
from app.models.enums import Category, Channel, Priority, ReviewReason, TicketStatus


@dataclass(frozen=True)
class TicketFilters:
    category: Category | None = None
    priority: Priority | None = None
    team: str | None = None
    channel: Channel | None = None
    status: TicketStatus | None = None


@dataclass(frozen=True)
class TicketView:
    """A ticket with its effective values: the latest correction, else the latest AI result."""

    ticket: Ticket
    category: Category | None
    priority: Priority | None
    team: str | None


@dataclass(frozen=True)
class TicketPage:
    items: list[TicketView]
    total: int


@dataclass(frozen=True)
class _EffectiveQuery:
    statement: Select[Any]
    category: ColumnElement[Any]
    priority: ColumnElement[Any]
    team: ColumnElement[Any]


def _effective_query() -> _EffectiveQuery:
    classification = (
        select(
            Classification.ticket_id,
            Classification.category,
            Classification.priority,
            Classification.team,
        )
        .distinct(Classification.ticket_id)
        .order_by(
            Classification.ticket_id,
            Classification.created_at.desc(),
            Classification.id.desc(),
        )
        .subquery()
    )
    correction = (
        select(
            Correction.ticket_id,
            Correction.new_category,
            Correction.new_priority,
            Correction.new_team,
        )
        .distinct(Correction.ticket_id)
        .order_by(
            Correction.ticket_id,
            Correction.corrected_at.desc(),
            Correction.id.desc(),
        )
        .subquery()
    )

    # CASE, not COALESCE: a correction may clear the team, and that must not bring back the AI's.
    is_corrected = correction.c.ticket_id.is_not(None)
    category = case((is_corrected, correction.c.new_category), else_=classification.c.category)
    priority = case((is_corrected, correction.c.new_priority), else_=classification.c.priority)
    team = case((is_corrected, correction.c.new_team), else_=classification.c.team)

    statement = (
        select(
            Ticket,
            category.label("effective_category"),
            priority.label("effective_priority"),
            team.label("effective_team"),
        )
        .outerjoin(classification, classification.c.ticket_id == Ticket.id)
        .outerjoin(correction, correction.c.ticket_id == Ticket.id)
    )
    return _EffectiveQuery(statement, category, priority, team)


class TicketRepository:
    """Ticket data access. Callers own the transaction: nothing here commits."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add_if_new(
        self,
        *,
        source_ticket_id: str,
        channel: Channel,
        created_at: datetime,
        customer_id: str,
        text_masked: str | None,
        import_job_id: uuid.UUID,
        status: TicketStatus = TicketStatus.PENDING,
        review_reason: ReviewReason | None = None,
    ) -> uuid.UUID | None:
        """Returns the new ticket's ID, or None if the source ID was already imported."""
        return self._session.scalar(
            insert(Ticket)
            .values(
                source_ticket_id=source_ticket_id,
                channel=channel,
                created_at=created_at,
                customer_id=customer_id,
                text_masked=text_masked,
                import_job_id=import_job_id,
                status=status,
                review_reason=review_reason,
            )
            .on_conflict_do_nothing(index_elements=[Ticket.source_ticket_id])
            .returning(Ticket.id)
        )

    def get(self, ticket_id: uuid.UUID) -> TicketView | None:
        """Loads the ticket with its AI results and correction history."""
        row = self._session.execute(
            _effective_query()
            .statement.where(Ticket.id == ticket_id)
            .options(selectinload(Ticket.classifications), selectinload(Ticket.corrections))
        ).one_or_none()
        return TicketView(*row) if row else None

    def list_tickets(self, filters: TicketFilters, limit: int, offset: int) -> TicketPage:
        """Queue order: priority, then oldest first. Manual review is a separate list, read
        with `status=needs_review` and ordered oldest first (TRD section 6)."""
        query = _effective_query()
        statement = query.statement

        if filters.status is None:
            statement = statement.where(Ticket.status != TicketStatus.NEEDS_REVIEW)
        else:
            statement = statement.where(Ticket.status == filters.status)
        if filters.channel is not None:
            statement = statement.where(Ticket.channel == filters.channel)
        if filters.category is not None:
            statement = statement.where(query.category == filters.category)
        if filters.priority is not None:
            statement = statement.where(query.priority == filters.priority)
        if filters.team is not None:
            statement = statement.where(query.team == filters.team)

        total = self._session.scalar(select(func.count()).select_from(statement.subquery()))

        ordering = [Ticket.created_at, Ticket.id]
        if filters.status is not TicketStatus.NEEDS_REVIEW:
            ordering.insert(0, query.priority.asc().nulls_last())
        rows = self._session.execute(statement.order_by(*ordering).limit(limit).offset(offset))
        return TicketPage(items=[TicketView(*row) for row in rows], total=total or 0)

    def add_classification(self, classification: Classification) -> None:
        self._session.add(classification)
        self._session.flush()

    def add_correction(self, correction: Correction) -> None:
        self._session.add(correction)
        self._session.flush()

    def claim_pending(self, limit: int, now: datetime) -> list[Ticket]:
        """Takes the oldest pending tickets. Locked rows are skipped, so workers never share one."""
        tickets = list(
            self._session.scalars(
                select(Ticket)
                .where(Ticket.status == TicketStatus.PENDING)
                .order_by(Ticket.created_at, Ticket.id)
                .limit(limit)
                .with_for_update(skip_locked=True)
            )
        )
        for ticket in tickets:
            ticket.status = TicketStatus.PROCESSING
            ticket.processing_started_at = now
            ticket.attempts += 1
        self._session.flush()
        return tickets

    def requeue_stale(self, started_before: datetime) -> int:
        """Returns tickets left in `processing` by a stopped worker to `pending`."""
        result = self._session.execute(
            update(Ticket)
            .where(
                Ticket.status == TicketStatus.PROCESSING,
                Ticket.processing_started_at < started_before,
            )
            .values(status=TicketStatus.PENDING, processing_started_at=None)
        )
        return result.rowcount

    def delete_ingested_before(self, cutoff: datetime) -> list[uuid.UUID]:
        """Deletes expired tickets and, by cascade, their history. Returns the deleted IDs."""
        return list(
            self._session.scalars(
                delete(Ticket).where(Ticket.ingested_at < cutoff).returning(Ticket.id)
            )
        )
