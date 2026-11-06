import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import (
    UUID,
    ColumnElement,
    Select,
    case,
    cast,
    delete,
    exists,
    func,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import ARRAY, array, insert
from sqlalchemy.orm import Session, selectinload

from app.models import Classification, Correction, Ticket
from app.models.enums import Category, Channel, Priority, ReviewReason, TicketStatus
from app.schemas.tickets import CountRow, StatsResponse


@dataclass(frozen=True)
class TicketFilters:
    category: Category | None = None
    priority: Priority | None = None
    team: str | None = None
    channel: Channel | None = None
    status: TicketStatus | None = None
    # Search results, best first. When set, these are the only tickets, in this order.
    ranked_ids: list[uuid.UUID] | None = None


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

        if filters.status is not None:
            statement = statement.where(Ticket.status == filters.status)
        elif filters.ranked_ids is None:
            statement = statement.where(Ticket.status != TicketStatus.NEEDS_REVIEW)
        if filters.ranked_ids is not None:
            statement = statement.where(Ticket.id.in_(filters.ranked_ids))
        if filters.channel is not None:
            statement = statement.where(Ticket.channel == filters.channel)
        if filters.category is not None:
            statement = statement.where(query.category == filters.category)
        if filters.priority is not None:
            statement = statement.where(query.priority == filters.priority)
        if filters.team is not None:
            statement = statement.where(query.team == filters.team)

        total = self._session.scalar(select(func.count()).select_from(statement.subquery()))

        ordering: list[Any] = [Ticket.created_at, Ticket.id]
        if filters.ranked_ids is not None:
            ranking = cast(array(filters.ranked_ids, type_=UUID), ARRAY(UUID))
            ordering.insert(0, func.array_position(ranking, Ticket.id))
        elif filters.status is not TicketStatus.NEEDS_REVIEW:
            ordering.insert(0, query.priority.asc().nulls_last())
        rows = self._session.execute(
            statement.options(selectinload(Ticket.classifications))
            .order_by(*ordering)
            .limit(limit)
            .offset(offset)
        )
        return TicketPage(items=[TicketView(*row) for row in rows], total=total or 0)

    def stats(self, start: datetime | None, end: datetime | None) -> StatsResponse:
        """Definitions: TRD section 6. Grouped by effective values."""
        statement = _effective_query().statement
        if start is not None:
            statement = statement.where(Ticket.ingested_at >= start)
        if end is not None:
            statement = statement.where(Ticket.ingested_at < end)
        tickets = statement.subquery()

        def counts(column: ColumnElement[Any]) -> list[CountRow]:
            rows = self._session.execute(
                select(column, func.count()).group_by(column).order_by(func.count().desc())
            )
            return [
                CountRow(name=None if name is None else str(name), count=count)
                for name, count in rows
            ]

        classified = exists().where(Classification.ticket_id == tickets.c.id)
        corrected = exists().where(Correction.ticket_id == tickets.c.id)
        totals = self._session.execute(
            select(
                func.count().label("total"),
                func.count().filter(tickets.c.review_reason.is_not(None)).label("review"),
                func.count().filter(classified).label("ai"),
                func.count().filter(classified, corrected).label("corrected"),
                func.count(tickets.c.classified_at).label("routed"),
                func.avg(
                    func.extract("epoch", tickets.c.classified_at - tickets.c.ingested_at)
                ).label("routing_seconds"),
            )
        ).one()

        return StatsResponse(
            total=totals.total,
            by_status=counts(tickets.c.status),
            by_team=counts(tickets.c.effective_team),
            by_category=counts(tickets.c.effective_category),
            by_priority=counts(tickets.c.effective_priority),
            review_total=totals.review,
            review_share=totals.review / totals.total if totals.total else 0,
            ai_classified=totals.ai,
            corrected=totals.corrected,
            correction_share=totals.corrected / totals.ai if totals.ai else 0,
            routing_count=totals.routed,
            routing_seconds_avg=(
                None if totals.routing_seconds is None else float(totals.routing_seconds)
            ),
        )

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

    def requeue_failed(self, ticket_id: uuid.UUID) -> bool:
        """Queues a ticket again after a model failure (TRD section 6). Other tickets stay where
        they are, so one held as a suspected injection cannot be sent to a model this way."""
        requeued = self._session.scalar(
            update(Ticket)
            .where(
                Ticket.id == ticket_id,
                Ticket.status == TicketStatus.NEEDS_REVIEW,
                Ticket.review_reason.in_((ReviewReason.LLM_UNAVAILABLE, ReviewReason.SCHEMA_ERROR)),
            )
            .values(status=TicketStatus.PENDING, review_reason=None)
            .returning(Ticket.id)
        )
        return requeued is not None

    def delete_ingested_before(self, cutoff: datetime) -> list[uuid.UUID]:
        """Deletes expired tickets and, by cascade, their history. Returns the deleted IDs."""
        return list(
            self._session.scalars(
                delete(Ticket).where(Ticket.ingested_at < cutoff).returning(Ticket.id)
            )
        )
