import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import CATEGORY_TYPE, PRIORITY_TYPE, Category, Priority
from app.models.ticket import Ticket


class Classification(Base):
    """An AI result. Never changed after it is written (TRD section 5)."""

    __tablename__ = "classifications"
    __table_args__ = (
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="confidence_range"),
        CheckConstraint(
            "latency_ms >= 0 AND input_tokens >= 0 AND output_tokens >= 0",
            name="usage_non_negative",
        ),
        Index("ix_classifications_ticket_id_created_at", "ticket_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tickets.id", ondelete="CASCADE"))
    model: Mapped[str] = mapped_column(String(128))
    prompt_version: Mapped[str] = mapped_column(String(64))
    category: Mapped[Category] = mapped_column(CATEGORY_TYPE)
    priority: Mapped[Priority] = mapped_column(PRIORITY_TYPE)
    confidence: Mapped[float]
    summary: Mapped[str] = mapped_column(Text)
    # Empty when the result goes to manual review instead of being routed (TRD section 4).
    team: Mapped[str | None] = mapped_column(String(64))
    latency_ms: Mapped[int]
    input_tokens: Mapped[int]
    output_tokens: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    ticket: Mapped[Ticket] = relationship(back_populates="classifications")
