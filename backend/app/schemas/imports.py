import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.enums import ImportStatus


class ImportJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    status: ImportStatus
    total: int
    inserted: int
    skipped: int
    errors: list[dict[str, Any]]
    created_at: datetime
    finished_at: datetime | None
