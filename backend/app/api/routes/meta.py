from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_routing
from app.classification.routing import RoutingTable
from app.models import User
from app.models.enums import Category, Channel, Priority, TicketStatus
from app.schemas.tickets import MetaResponse

router = APIRouter(prefix="/meta", tags=["meta"])


@router.get("")
def get_meta(
    _: Annotated[User, Depends(get_current_user)],
    routing: Annotated[RoutingTable, Depends(get_routing)],
) -> MetaResponse:
    return MetaResponse(
        categories=list(Category),
        priorities=list(Priority),
        channels=list(Channel),
        statuses=list(TicketStatus),
        teams=sorted(set(routing.teams.values())),
        routing=routing.teams,
    )
