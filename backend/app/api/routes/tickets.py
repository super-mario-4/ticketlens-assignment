import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user, get_ticket_service, require_operator
from app.models import User
from app.models.enums import Category, Channel, Priority, TicketStatus
from app.repositories.tickets import TicketFilters, TicketView
from app.schemas.tickets import (
    ClassificationResponse,
    CorrectionRequest,
    CorrectionResponse,
    ReclassifyResponse,
    TicketDetail,
    TicketItem,
    TicketPageResponse,
)
from app.search.client import SearchError
from app.services.tickets import (
    InvalidTeamError,
    SearchPageRequest,
    TicketNotCorrectableError,
    TicketNotFoundError,
    TicketNotReclassifiableError,
    TicketService,
    latest_classification,
    preview,
)

router = APIRouter(prefix="/tickets", tags=["tickets"])


def _item_fields(view: TicketView) -> dict[str, object]:
    ticket = view.ticket
    classification = latest_classification(view)
    return {
        "id": ticket.id,
        "source_ticket_id": ticket.source_ticket_id,
        "channel": ticket.channel,
        "created_at": ticket.created_at,
        "status": ticket.status,
        "review_reason": ticket.review_reason,
        "category": view.category,
        "priority": view.priority,
        "team": view.team,
        "summary": classification.summary if classification else None,
        "confidence": classification.confidence if classification else None,
        "preview": preview(ticket.text_masked),
    }


def _detail(view: TicketView) -> TicketDetail:
    ticket = view.ticket
    return TicketDetail(
        **_item_fields(view),
        text_masked=ticket.text_masked,
        ingested_at=ticket.ingested_at,
        classified_at=ticket.classified_at,
        classifications=[
            ClassificationResponse.model_validate(item) for item in ticket.classifications
        ],
        corrections=[
            CorrectionResponse(
                old_category=item.old_category,
                new_category=item.new_category,
                old_priority=item.old_priority,
                new_priority=item.new_priority,
                old_team=item.old_team,
                new_team=item.new_team,
                reason=item.reason,
                corrected_by=item.corrector.username,
                corrected_at=item.corrected_at,
            )
            for item in ticket.corrections
        ],
    )


@router.get("")
def list_tickets(
    _: Annotated[User, Depends(get_current_user)],
    service: Annotated[TicketService, Depends(get_ticket_service)],
    category: Category | None = None,
    priority: Priority | None = None,
    team: str | None = None,
    channel: Channel | None = None,
    ticket_status: Annotated[TicketStatus | None, Query(alias="status")] = None,
    q: Annotated[str | None, Query(max_length=200)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> TicketPageResponse:
    """The queue, or with `status=needs_review` the manual review list."""
    filters = TicketFilters(category, priority, team, channel, ticket_status)
    query = q.strip() if q else None
    try:
        page = service.list(SearchPageRequest(filters, limit, offset, query))
    except SearchError:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, {"code": "search_unavailable"}
        ) from None
    return TicketPageResponse(
        items=[TicketItem(**_item_fields(view)) for view in page.items],
        total=page.total,
        limit=limit,
        offset=offset,
    )


@router.get("/{ticket_id}")
def get_ticket(
    ticket_id: uuid.UUID,
    _: Annotated[User, Depends(get_current_user)],
    service: Annotated[TicketService, Depends(get_ticket_service)],
) -> TicketDetail:
    try:
        return _detail(service.get(ticket_id))
    except TicketNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, {"code": "ticket_not_found"}) from None


@router.patch("/{ticket_id}/classification")
def correct_ticket(
    ticket_id: uuid.UUID,
    correction: CorrectionRequest,
    user: Annotated[User, Depends(require_operator)],
    service: Annotated[TicketService, Depends(get_ticket_service)],
) -> TicketDetail:
    try:
        return _detail(service.correct(ticket_id, correction, user))
    except TicketNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, {"code": "ticket_not_found"}) from None
    except TicketNotCorrectableError:
        raise HTTPException(status.HTTP_409_CONFLICT, {"code": "ticket_not_correctable"}) from None
    except InvalidTeamError:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, {"code": "invalid_team"}
        ) from None


@router.post("/{ticket_id}/reclassify", status_code=status.HTTP_202_ACCEPTED)
def reclassify(
    ticket_id: uuid.UUID,
    _: Annotated[User, Depends(require_operator)],
    service: Annotated[TicketService, Depends(get_ticket_service)],
) -> ReclassifyResponse:
    """Queues a ticket held as `llm_unavailable` or `schema_error` for the worker."""
    try:
        service.reclassify(ticket_id)
    except TicketNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, {"code": "ticket_not_found"}) from None
    except TicketNotReclassifiableError:
        raise HTTPException(
            status.HTTP_409_CONFLICT, {"code": "ticket_not_reclassifiable"}
        ) from None
    return ReclassifyResponse(id=ticket_id, status=TicketStatus.PENDING)
