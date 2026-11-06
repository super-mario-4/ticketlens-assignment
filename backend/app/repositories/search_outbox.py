import uuid
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import SearchIndexOutbox, Ticket
from app.models.enums import OutboxOperation, OutboxStatus


class SearchOutboxRepository:
    """Callers own the transaction: nothing here commits."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, ticket_id: uuid.UUID, operation: OutboxOperation) -> None:
        self._session.add(SearchIndexOutbox(ticket_id=ticket_id, operation=operation))

    def claim(self, limit: int) -> list[tuple[SearchIndexOutbox, str | None]]:
        """Oldest open tasks with the text of their ticket. Failed tasks are tried again."""
        rows = self._session.execute(
            select(SearchIndexOutbox, Ticket.text_masked)
            .outerjoin(Ticket, Ticket.id == SearchIndexOutbox.ticket_id)
            .where(SearchIndexOutbox.status != OutboxStatus.DONE)
            .order_by(SearchIndexOutbox.created_at, SearchIndexOutbox.id)
            .limit(limit)
            .with_for_update(of=SearchIndexOutbox, skip_locked=True)
        )
        return [(row[0], row[1]) for row in rows]

    def delete_done_before(self, cutoff: datetime) -> None:
        self._session.execute(
            delete(SearchIndexOutbox).where(
                SearchIndexOutbox.status == OutboxStatus.DONE,
                SearchIndexOutbox.processed_at < cutoff,
            )
        )
