import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import (
    CHANNEL_TYPE,
    REVIEW_REASON_TYPE,
    TICKET_STATUS_TYPE,
    Channel,
    ReviewReason,
    TicketStatus,
)
from app.models.import_job import ImportJob

if TYPE_CHECKING:
    from app.models.classification import Classification
    from app.models.correction import Correction


class Ticket(Base):
    """A customer message. Category, priority and team come from `classifications` and
    `corrections`, never from this table (TRD sections 5 and 6)."""

    __tablename__ = "tickets"
    __table_args__ = (
        CheckConstraint("attempts >= 0", name="attempts_non_negative"),
        CheckConstraint(
            "status <> 'needs_review' OR review_reason IS NOT NULL",
            name="needs_review_has_reason",
        ),
        CheckConstraint(
            "status <> 'processing' OR processing_started_at IS NOT NULL",
            name="processing_has_start_time",
        ),
        CheckConstraint(
            "text_masked IS NOT NULL OR review_reason IS NOT DISTINCT FROM 'masking_error'",
            name="text_required_unless_masking_error",
        ),
        Index("ix_tickets_status_created_at", "status", "created_at"),
        Index("ix_tickets_channel_created_at", "channel", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source_ticket_id: Mapped[str] = mapped_column(String(64), unique=True)
    channel: Mapped[Channel] = mapped_column(CHANNEL_TYPE)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    customer_id: Mapped[str] = mapped_column(String(64))
    text_masked: Mapped[str | None] = mapped_column(Text)
    status: Mapped[TicketStatus] = mapped_column(TICKET_STATUS_TYPE, default=TicketStatus.PENDING)
    review_reason: Mapped[ReviewReason | None] = mapped_column(REVIEW_REASON_TYPE)
    attempts: Mapped[int] = mapped_column(default=0, server_default="0")
    import_job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("import_jobs.id", ondelete="RESTRICT"), index=True
    )
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    processing_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    classified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    import_job: Mapped[ImportJob] = relationship()
    classifications: Mapped[list["Classification"]] = relationship(
        back_populates="ticket",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Classification.created_at, Classification.id",
    )
    corrections: Mapped[list["Correction"]] = relationship(
        back_populates="ticket",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Correction.corrected_at, Correction.id",
    )
