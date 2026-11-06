import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.enums import OutboxOperation
from app.repositories.search_outbox import SearchOutboxRepository
from app.repositories.tickets import TicketRepository

logger = logging.getLogger(__name__)


class RetentionService:
    """Deletes expired tickets with their history and search documents (TRD section 8)."""

    def __init__(
        self,
        session: Session,
        tickets: TicketRepository,
        outbox: SearchOutboxRepository,
        settings: Settings,
    ) -> None:
        self._session = session
        self._tickets = tickets
        self._outbox = outbox
        self._settings = settings

    def clean(self) -> int:
        cutoff = datetime.now(UTC) - timedelta(days=self._settings.retention_days)
        deleted = self._tickets.delete_ingested_before(cutoff)
        for ticket_id in deleted:
            self._outbox.add(ticket_id, OutboxOperation.DELETE)
        self._outbox.delete_done_before(cutoff)
        self._session.commit()
        logger.info("Retention removed %d tickets", len(deleted))
        return len(deleted)
