import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import CATEGORY_TYPE, PRIORITY_TYPE, Category, Priority
from app.models.ticket import Ticket
from app.models.user import User


class Correction(Base):
    """One operator correction. Append-only history (TRD section 5)."""

    __tablename__ = "corrections"
    __table_args__ = (
        Index("ix_corrections_ticket_id_corrected_at", "ticket_id", "corrected_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tickets.id", ondelete="CASCADE"))
    # `old_*` are empty when the ticket had no AI result.
    old_category: Mapped[Category | None] = mapped_column(CATEGORY_TYPE)
    new_category: Mapped[Category] = mapped_column(CATEGORY_TYPE)
    old_priority: Mapped[Priority | None] = mapped_column(PRIORITY_TYPE)
    new_priority: Mapped[Priority] = mapped_column(PRIORITY_TYPE)
    old_team: Mapped[str | None] = mapped_column(String(64))
    # Empty for `other`, which has no team (PRD section 7).
    new_team: Mapped[str | None] = mapped_column(String(64))
    reason: Mapped[str | None] = mapped_column(Text)
    corrected_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    corrected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    ticket: Mapped[Ticket] = relationship(back_populates="corrections")
    corrector: Mapped[User] = relationship()
