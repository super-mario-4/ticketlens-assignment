import uuid
from dataclasses import dataclass, replace
from datetime import datetime

from sqlalchemy.orm import Session

from app.classification.routing import RoutingTable
from app.core.config import Settings
from app.models import Classification, Correction, User
from app.models.enums import Category, TicketStatus
from app.preprocess.mask import mask_sensitive_data
from app.repositories.tickets import TicketFilters, TicketPage, TicketRepository, TicketView
from app.schemas.tickets import CorrectionRequest, StatsResponse
from app.search.client import SearchClient

_PREVIEW_LENGTH = 160


class TicketNotFoundError(Exception):
    pass


class TicketNotReclassifiableError(Exception):
    pass


class TicketNotCorrectableError(Exception):
    pass


class InvalidTeamError(Exception):
    pass


def latest_classification(view: TicketView) -> Classification | None:
    return view.ticket.classifications[-1] if view.ticket.classifications else None


def preview(text: str | None) -> str | None:
    return text[:_PREVIEW_LENGTH] if text else text


@dataclass(frozen=True)
class SearchPageRequest:
    filters: TicketFilters
    limit: int
    offset: int
    query: str | None = None


class TicketService:
    def __init__(
        self,
        session: Session,
        tickets: TicketRepository,
        search: SearchClient,
        routing: RoutingTable,
        settings: Settings,
    ) -> None:
        self._session = session
        self._tickets = tickets
        self._search = search
        self._routing = routing
        self._settings = settings

    def list(self, request: SearchPageRequest) -> TicketPage:
        """Elasticsearch finds and ranks; PostgreSQL filters and pages (TRD section 3)."""
        filters = request.filters
        if request.query:
            ranked = self._search.search(request.query, self._settings.search_max_hits)
            filters = replace(filters, ranked_ids=ranked)
        return self._tickets.list_tickets(filters, request.limit, request.offset)

    def get(self, ticket_id: uuid.UUID) -> TicketView:
        view = self._tickets.get(ticket_id)
        if view is None:
            raise TicketNotFoundError
        return view

    def reclassify(self, ticket_id: uuid.UUID) -> None:
        """Queues a ticket again after a model failure, so the worker classifies it."""
        if self._tickets.requeue_failed(ticket_id):
            self._session.commit()
            return
        if self._tickets.get(ticket_id) is None:
            raise TicketNotFoundError
        raise TicketNotReclassifiableError

    def correct(self, ticket_id: uuid.UUID, request: CorrectionRequest, user: User) -> TicketView:
        """Adds to the correction history; the AI result stays. A reviewed ticket moves to
        `classified` and keeps its `review_reason` for statistics (TRD section 5)."""
        view = self.get(ticket_id)
        ticket = view.ticket
        if ticket.status in (TicketStatus.PENDING, TicketStatus.PROCESSING):
            raise TicketNotCorrectableError

        self._tickets.add_correction(
            Correction(
                ticket_id=ticket.id,
                old_category=view.category,
                new_category=request.category,
                old_priority=view.priority,
                new_priority=request.priority,
                old_team=view.team,
                new_team=self._team_for(request),
                reason=mask_sensitive_data(request.reason) if request.reason else None,
                corrected_by=user.id,
            )
        )
        ticket.status = TicketStatus.CLASSIFIED
        self._session.commit()
        self._session.expire_all()
        return self.get(ticket_id)

    def stats(self, start: datetime | None, end: datetime | None) -> StatsResponse:
        return self._tickets.stats(start, end)

    def _team_for(self, request: CorrectionRequest) -> str | None:
        if request.team is None:
            if request.category is Category.OTHER:
                return None
            return self._routing.team_for(request.category)
        if request.team not in self._routing.teams.values():
            raise InvalidTeamError
        return request.team
