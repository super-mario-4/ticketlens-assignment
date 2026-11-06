import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import Category, Channel, Priority, ReviewReason, TicketStatus


class ReclassifyResponse(BaseModel):
    id: uuid.UUID
    status: TicketStatus


class TicketItem(BaseModel):
    """One queue row. Category, priority and team are the effective values (TRD section 6)."""

    id: uuid.UUID
    source_ticket_id: str
    channel: Channel
    created_at: datetime
    status: TicketStatus
    review_reason: ReviewReason | None
    category: Category | None
    priority: Priority | None
    team: str | None
    summary: str | None
    confidence: float | None
    preview: str | None


class TicketPageResponse(BaseModel):
    items: list[TicketItem]
    total: int
    limit: int
    offset: int


class ClassificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    model: str
    prompt_version: str
    category: Category
    priority: Priority
    confidence: float
    summary: str
    team: str | None
    latency_ms: int
    created_at: datetime


class CorrectionResponse(BaseModel):
    old_category: Category | None
    new_category: Category
    old_priority: Priority | None
    new_priority: Priority
    old_team: str | None
    new_team: str | None
    reason: str | None
    corrected_by: str
    corrected_at: datetime


class TicketDetail(TicketItem):
    text_masked: str | None
    ingested_at: datetime
    classified_at: datetime | None
    classifications: list[ClassificationResponse]
    corrections: list[CorrectionResponse]


class CorrectionRequest(BaseModel):
    """Without a team, the team comes from the routing file."""

    category: Category
    priority: Priority
    team: str | None = Field(default=None, max_length=64)
    reason: str | None = Field(default=None, max_length=1000)


class MetaResponse(BaseModel):
    """The allowed values, so the screen has no list of its own (TRD section 5)."""

    categories: list[Category]
    priorities: list[Priority]
    channels: list[Channel]
    statuses: list[TicketStatus]
    teams: list[str]
    routing: dict[Category, str]


class CountRow(BaseModel):
    name: str | None
    count: int


class StatsResponse(BaseModel):
    total: int
    by_status: list[CountRow]
    by_team: list[CountRow]
    by_category: list[CountRow]
    by_priority: list[CountRow]
    review_total: int
    review_share: float
    ai_classified: int
    corrected: int
    correction_share: float
    routing_count: int
    routing_seconds_avg: float | None
