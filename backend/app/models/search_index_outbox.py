import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import (
    OUTBOX_OPERATION_TYPE,
    OUTBOX_STATUS_TYPE,
    OutboxOperation,
    OutboxStatus,
)


class SearchIndexOutbox(Base):
    """Search index work saved with the ticket, so a stopped Elasticsearch loses nothing (TRD
    section 3). No foreign key: a delete task must outlive the ticket it removes."""

    __tablename__ = "search_index_outbox"
    __table_args__ = (Index("ix_search_index_outbox_status_created_at", "status", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID]
    operation: Mapped[OutboxOperation] = mapped_column(OUTBOX_OPERATION_TYPE)
    status: Mapped[OutboxStatus] = mapped_column(OUTBOX_STATUS_TYPE, default=OutboxStatus.PENDING)
    attempts: Mapped[int] = mapped_column(default=0, server_default="0")
    # An error type only, never a message: messages can quote ticket text.
    last_error: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
