import logging
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.enums import OutboxOperation, OutboxStatus
from app.repositories.search_outbox import SearchOutboxRepository
from app.search.client import SearchClient, SearchDocument, SearchError

logger = logging.getLogger(__name__)


class SearchIndexService:
    def __init__(
        self, session: Session, outbox: SearchOutboxRepository, client: SearchClient
    ) -> None:
        self._session = session
        self._outbox = outbox
        self._client = client

    def process_batch(self, limit: int) -> int:
        """Returns how many tasks finished. On failure they stay open for the next run."""
        rows = self._outbox.claim(limit)
        if not rows:
            self._session.rollback()
            return 0

        documents = [
            SearchDocument(
                task.ticket_id, text if task.operation is OutboxOperation.INDEX else None
            )
            for task, text in rows
        ]
        try:
            self._client.ensure_index()
            self._client.write(documents)
        except SearchError as error:
            for task, _ in rows:
                task.status = OutboxStatus.FAILED
                task.attempts += 1
                task.last_error = str(error)[:128]
            self._session.commit()
            logger.warning("Search indexing failed for %d tasks: %s", len(rows), error)
            return 0

        now = datetime.now(UTC)
        for task, _ in rows:
            task.status = OutboxStatus.DONE
            task.attempts += 1
            task.processed_at = now
            task.last_error = None
        self._session.commit()
        return len(rows)
