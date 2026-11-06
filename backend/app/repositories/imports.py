import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ImportJob
from app.models.enums import ImportStatus


class ImportRepository:
    """Import job data access. Callers own the transaction: nothing here commits."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, job: ImportJob) -> None:
        self._session.add(job)
        self._session.flush()

    def get(self, job_id: uuid.UUID) -> ImportJob | None:
        return self._session.get(ImportJob, job_id)

    def list_unfinished(self) -> list[ImportJob]:
        return list(
            self._session.scalars(
                select(ImportJob).where(ImportJob.status == ImportStatus.PROCESSING)
            )
        )

    def mark_failed(self, job: ImportJob, code: str, now: datetime) -> None:
        job.status = ImportStatus.FAILED
        job.errors = [*job.errors, {"code": code}]
        job.finished_at = now
        self._session.flush()
