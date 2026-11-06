import csv
import io
import logging
import re
import uuid
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import PureWindowsPath
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import ImportJob, User
from app.models.enums import Channel, ImportStatus, OutboxOperation
from app.preprocess.mask import contains_sensitive_data
from app.preprocess.pipeline import prepare_text
from app.repositories.imports import ImportRepository
from app.repositories.search_outbox import SearchOutboxRepository
from app.repositories.tickets import TicketRepository

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = ("id", "channel", "created_at", "text", "customer_id")
_IDENTIFIER = re.compile(r"[A-Za-z0-9_-]{1,64}")

# A file is already capped by size, so a single long field needs no separate limit.
csv.field_size_limit(2**31 - 1)


class ImportFileError(Exception):
    """The file cannot be imported at all, so no job is started (TRD section 11)."""

    def __init__(self, code: str, **details: Any) -> None:
        super().__init__(code)
        self.detail = {"code": code, **details}


class _RowError(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class _Row:
    source_ticket_id: str
    channel: Channel
    created_at: datetime
    text: str
    customer_id: str


@dataclass
class _Batch:
    total: int = 0
    inserted: int = 0
    skipped: int = 0
    errors: list[dict[str, Any]] = field(default_factory=list)


def _identifier(value: str, code: str) -> str:
    """These columns are stored as they are, so they must not carry sensitive data."""
    value = value.strip()
    if not _IDENTIFIER.fullmatch(value) or contains_sensitive_data(value):
        raise _RowError(code)
    return value


def _parse_row(values: list[str], positions: dict[str, int]) -> _Row:
    if len(values) != len(positions):
        raise _RowError("wrong_column_count")

    source_ticket_id = _identifier(values[positions["id"]], "invalid_id")
    try:
        channel = Channel(values[positions["channel"]].strip())
    except ValueError:
        raise _RowError("invalid_channel") from None
    try:
        created_at = datetime.fromisoformat(values[positions["created_at"]].strip())
    except ValueError:
        raise _RowError("invalid_created_at") from None
    if created_at.tzinfo is None:
        raise _RowError("invalid_created_at")

    return _Row(
        source_ticket_id=source_ticket_id,
        channel=channel,
        created_at=created_at,
        text=values[positions["text"]],
        customer_id=_identifier(values[positions["customer_id"]], "invalid_customer_id"),
    )


def _safe_filename(filename: str) -> str:
    name = PureWindowsPath(filename).name.strip()
    if not name.lower().endswith(".csv") or len(name) > 255:
        raise ImportFileError("invalid_filename")
    return name


def _open_reader(content: bytes) -> tuple[Iterator[list[str]], dict[str, int]]:
    """Checks everything that decides whether the import starts."""
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ImportFileError("invalid_encoding") from None
    if "\x00" in text:
        raise ImportFileError("invalid_file_format")
    if not text.strip():
        raise ImportFileError("empty_file")

    reader = csv.reader(io.StringIO(text, newline=""), strict=True)
    try:
        header = [name.strip() for name in next(reader)]
    except csv.Error:
        raise ImportFileError("malformed_csv") from None

    missing = [name for name in REQUIRED_COLUMNS if name not in header]
    if missing:
        raise ImportFileError("missing_columns", columns=missing)
    # Unknown names are not echoed: in a file with no header row they would be ticket data.
    if len(header) != len(REQUIRED_COLUMNS):
        raise ImportFileError("unexpected_columns")
    return reader, {name: position for position, name in enumerate(header)}


class ImportService:
    def __init__(
        self,
        session: Session,
        imports: ImportRepository,
        tickets: TicketRepository,
        settings: Settings,
        outbox: SearchOutboxRepository,
    ) -> None:
        self._session = session
        self._imports = imports
        self._tickets = tickets
        self._settings = settings
        self._outbox = outbox

    def get(self, job_id: uuid.UUID) -> ImportJob | None:
        return self._imports.get(job_id)

    def run(self, content: bytes, filename: str, user: User) -> ImportJob:
        name = _safe_filename(filename)
        reader, positions = _open_reader(content)

        job = ImportJob(filename=name, created_by=user.id)
        self._imports.add(job)
        self._session.commit()

        try:
            self._import_rows(job, reader, positions)
        except csv.Error:
            self._fail(job, "malformed_csv")
        except SQLAlchemyError as exc:
            logger.warning("Import job %s failed: %s", job.id, type(exc).__name__)
            self._fail(job, "import_failed")
        return job

    def recover_interrupted(self) -> int:
        """A job still open at startup lost its process. Finished batches are kept, and
        importing the file again adds only the rest."""
        jobs = self._imports.list_unfinished()
        for job in jobs:
            self._imports.mark_failed(job, "interrupted", datetime.now(UTC))
        self._session.commit()
        return len(jobs)

    def _import_rows(
        self, job: ImportJob, reader: Iterator[list[str]], positions: dict[str, int]
    ) -> None:
        batch = _Batch()
        for values in reader:
            if not values:  # A blank line, such as the one at the end of a file.
                continue
            self._import_row(job, values, positions, batch, reader.line_num)  # type: ignore[attr-defined]
            if batch.total >= self._settings.import_batch_size:
                self._save(job, batch)
                batch = _Batch()

        self._save(job, batch)
        job.status = ImportStatus.COMPLETED
        job.finished_at = datetime.now(UTC)
        self._session.commit()

    def _import_row(
        self,
        job: ImportJob,
        values: list[str],
        positions: dict[str, int],
        batch: _Batch,
        line: int,
    ) -> None:
        batch.total += 1
        try:
            row = _parse_row(values, positions)
        except _RowError as error:
            batch.skipped += 1
            batch.errors.append({"row": line, "code": error.code})
            return

        prepared = prepare_text(row.text, self._settings.max_ticket_text_length)
        ticket_id = self._tickets.add_if_new(
            source_ticket_id=row.source_ticket_id,
            channel=row.channel,
            created_at=row.created_at,
            customer_id=row.customer_id,
            text_masked=prepared.text_masked,
            import_job_id=job.id,
            status=prepared.status,
            review_reason=prepared.review_reason,
        )
        if ticket_id is None:
            batch.skipped += 1
            return
        batch.inserted += 1
        if prepared.text_masked is None:
            batch.errors.append({"row": line, "id": row.source_ticket_id, "code": "masking_error"})
        else:
            self._outbox.add(ticket_id, OutboxOperation.INDEX)

    def _save(self, job: ImportJob, batch: _Batch) -> None:
        """Counts and tickets commit together, so a job never reports rows it did not keep."""
        job.total += batch.total
        job.inserted += batch.inserted
        job.skipped += batch.skipped
        if batch.errors:
            job.errors = [*job.errors, *batch.errors]
        self._session.commit()

    def _fail(self, job: ImportJob, code: str) -> None:
        self._session.rollback()
        self._imports.mark_failed(job, code, datetime.now(UTC))
        self._session.commit()
