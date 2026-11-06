import logging

import httpx
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class HealthRepository:
    """Checks whether the system's data stores can be reached."""

    def __init__(self, session: Session, elasticsearch_url: str, timeout_seconds: float) -> None:
        self._session = session
        self._elasticsearch_url = elasticsearch_url
        self._timeout_seconds = timeout_seconds

    def postgres_is_available(self) -> bool:
        try:
            self._session.execute(text("SELECT 1"))
        except SQLAlchemyError as exc:
            logger.warning("PostgreSQL health check failed: %s", type(exc).__name__)
            return False
        return True

    def elasticsearch_is_available(self) -> bool:
        try:
            response = httpx.get(
                f"{self._elasticsearch_url}/_cluster/health",
                timeout=self._timeout_seconds,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("Elasticsearch health check failed: %s", type(exc).__name__)
            return False
        return True
