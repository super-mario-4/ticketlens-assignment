from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_ticket_service, require_lead
from app.models import User
from app.schemas.tickets import StatsResponse
from app.services.tickets import TicketService

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("")
def get_stats(
    _: Annotated[User, Depends(require_lead)],
    service: Annotated[TicketService, Depends(get_ticket_service)],
    start: datetime | None = None,
    end: datetime | None = None,
) -> StatsResponse:
    """Figures for tickets ingested in the period (TRD section 6)."""
    return service.stats(start, end)
