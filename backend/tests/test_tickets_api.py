import uuid
from collections.abc import Iterator
from datetime import timedelta

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_search_client
from app.core.config import Settings, get_settings
from app.db.session import get_session_factory
from app.models import Classification, Correction, ImportJob, SearchIndexOutbox, Ticket, User
from app.models.enums import (
    Category,
    Channel,
    OutboxOperation,
    Priority,
    ReviewReason,
    TicketStatus,
)
from app.repositories.search_outbox import SearchOutboxRepository
from app.search.client import SearchClient, SearchDocument
from app.services.search_index import SearchIndexService
from tests.auth import authorized_app
from tests.factories import TICKET_TIME, build_classification, make_ticket


@pytest.fixture
def database(migrated_database: None) -> Iterator[Session]:
    with get_session_factory()() as session:
        yield session

    with get_session_factory()() as cleanup:
        for model in (Ticket, ImportJob, User, SearchIndexOutbox):
            cleanup.execute(delete(model))
        cleanup.commit()


@pytest.fixture
def api(database: Session) -> Iterator[TestClient]:
    with TestClient(authorized_app()) as client:
        yield client


def classified(session: Session, priority: Priority = Priority.HIGH, **overrides) -> Ticket:
    ticket = make_ticket(session, status=TicketStatus.CLASSIFIED, **overrides)
    session.add(build_classification(ticket, priority=priority))
    session.commit()
    return ticket


def held(session: Session, reason: ReviewReason = ReviewReason.LOW_CONFIDENCE) -> Ticket:
    ticket = make_ticket(session, status=TicketStatus.NEEDS_REVIEW, review_reason=reason)
    session.commit()
    return ticket


def correction(**overrides) -> dict[str, object]:
    return {"category": "security_fraud", "priority": "Critical"} | overrides


def test_queue_is_ordered_by_priority_then_age(api: TestClient, database: Session) -> None:
    low = classified(database, Priority.LOW)
    newer_high = classified(database, created_at=TICKET_TIME + timedelta(hours=1))
    older_high = classified(database, created_at=TICKET_TIME - timedelta(hours=1))
    critical = classified(database, Priority.CRITICAL)

    body = api.get("/api/tickets").json()

    assert [item["id"] for item in body["items"]] == [
        str(critical.id),
        str(older_high.id),
        str(newer_high.id),
        str(low.id),
    ]
    assert body["total"] == 4


def test_queue_item_shows_the_summary_and_values(api: TestClient, database: Session) -> None:
    classified(database)

    item = api.get("/api/tickets").json()["items"][0]

    assert item["category"] == "payments_transfers"
    assert item["priority"] == "High"
    assert item["team"] == "Payments"
    assert item["summary"] == "Mijoz o'tkazma yetib bormaganini yozgan."
    assert item["confidence"] == 0.86


def test_review_list_is_separate_and_oldest_first(api: TestClient, database: Session) -> None:
    classified(database)
    newer = held(database)
    older = make_ticket(
        database,
        status=TicketStatus.NEEDS_REVIEW,
        review_reason=ReviewReason.UNCLEAR,
        created_at=TICKET_TIME - timedelta(days=1),
    )
    database.commit()

    queue = api.get("/api/tickets").json()
    review = api.get("/api/tickets", params={"status": "needs_review"}).json()

    assert queue["total"] == 1
    assert [item["id"] for item in review["items"]] == [str(older.id), str(newer.id)]
    assert review["items"][0]["review_reason"] == "unclear"


def test_filters_apply_together(api: TestClient, database: Session) -> None:
    wanted = classified(database, Priority.CRITICAL, channel=Channel.EMAIL)
    classified(database, Priority.CRITICAL)
    classified(database, channel=Channel.EMAIL)

    body = api.get(
        "/api/tickets",
        params={"priority": "Critical", "channel": "email", "team": "Payments"},
    ).json()

    assert [item["id"] for item in body["items"]] == [str(wanted.id)]


def test_paging_keeps_the_total(api: TestClient, database: Session) -> None:
    for _ in range(3):
        classified(database)

    body = api.get("/api/tickets", params={"limit": 2, "offset": 2}).json()

    assert len(body["items"]) == 1
    assert body["total"] == 3
    assert (body["limit"], body["offset"]) == (2, 2)


@pytest.mark.parametrize("params", [{"limit": 101}, {"limit": 0}, {"offset": -1}])
def test_paging_limits_are_enforced(api: TestClient, params: dict[str, int]) -> None:
    assert api.get("/api/tickets", params=params).status_code == 422


def test_detail_has_text_ai_result_and_history(api: TestClient, database: Session) -> None:
    ticket = classified(database)
    api.patch(f"/api/tickets/{ticket.id}/classification", json=correction(reason="Noto'g'ri"))

    body = api.get(f"/api/tickets/{ticket.id}").json()

    assert body["text_masked"] == "Pulim yetib bormadi"
    assert len(body["classifications"]) == 1
    assert body["classifications"][0]["category"] == "payments_transfers"
    assert body["corrections"][0]["corrected_by"] == "system"
    assert body["corrections"][0]["old_team"] == "Payments"
    assert body["corrections"][0]["reason"] == "Noto'g'ri"


def test_unknown_ticket_is_404(api: TestClient) -> None:
    assert api.get(f"/api/tickets/{uuid.uuid4()}").status_code == 404
    response = api.patch(f"/api/tickets/{uuid.uuid4()}/classification", json=correction())
    assert response.status_code == 404


def test_correction_changes_the_effective_values_only(api: TestClient, database: Session) -> None:
    ticket = classified(database)

    body = api.patch(f"/api/tickets/{ticket.id}/classification", json=correction()).json()

    assert body["category"] == "security_fraud"
    assert body["priority"] == "Critical"
    assert body["team"] == "Security / Fraud"
    stored = database.scalars(select(Classification).where(Classification.ticket_id == ticket.id))
    assert stored.one().category is Category.PAYMENTS_TRANSFERS


def test_every_correction_is_kept(api: TestClient, database: Session) -> None:
    ticket = classified(database)
    url = f"/api/tickets/{ticket.id}/classification"

    api.patch(url, json=correction())
    api.patch(url, json=correction(category="refunds", priority="Low"))

    history = api.get(f"/api/tickets/{ticket.id}").json()["corrections"]
    assert [item["new_category"] for item in history] == ["security_fraud", "refunds"]
    assert history[1]["old_category"] == "security_fraud"
    assert api.get(f"/api/tickets/{ticket.id}").json()["team"] == "Refunds"


def test_corrected_values_drive_the_queue(api: TestClient, database: Session) -> None:
    ticket = classified(database, Priority.LOW)
    classified(database, Priority.HIGH)
    api.patch(f"/api/tickets/{ticket.id}/classification", json=correction())

    body = api.get("/api/tickets").json()

    assert body["items"][0]["id"] == str(ticket.id)
    filtered = api.get("/api/tickets", params={"team": "Security / Fraud"}).json()
    assert [item["id"] for item in filtered["items"]] == [str(ticket.id)]


def test_review_ticket_leaves_the_review_list_and_keeps_its_reason(
    api: TestClient, database: Session
) -> None:
    ticket = held(database, ReviewReason.INJECTION_SUSPECTED)

    body = api.patch(f"/api/tickets/{ticket.id}/classification", json=correction()).json()

    assert body["status"] == "classified"
    assert body["review_reason"] == "injection_suspected"
    assert body["corrections"][0]["old_category"] is None
    assert api.get("/api/tickets", params={"status": "needs_review"}).json()["total"] == 0


def test_operator_can_choose_another_team(api: TestClient, database: Session) -> None:
    ticket = classified(database)

    body = api.patch(
        f"/api/tickets/{ticket.id}/classification", json=correction(team="Cards")
    ).json()

    assert body["team"] == "Cards"


def test_unknown_team_is_refused(api: TestClient, database: Session) -> None:
    ticket = classified(database)

    response = api.patch(f"/api/tickets/{ticket.id}/classification", json=correction(team="Nobody"))

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "invalid_team"
    assert database.scalar(select(func.count()).select_from(Correction)) == 0


def test_other_has_no_team_by_default(api: TestClient, database: Session) -> None:
    ticket = held(database)

    body = api.patch(
        f"/api/tickets/{ticket.id}/classification", json=correction(category="other")
    ).json()

    assert body["team"] is None


@pytest.mark.parametrize("status", [TicketStatus.PENDING, TicketStatus.PROCESSING])
def test_ticket_still_in_the_queue_cannot_be_corrected(
    api: TestClient, database: Session, status: TicketStatus
) -> None:
    ticket = make_ticket(database, status=status, processing_started_at=TICKET_TIME)
    database.commit()

    response = api.patch(f"/api/tickets/{ticket.id}/classification", json=correction())

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "ticket_not_correctable"


def test_correction_reason_is_masked(api: TestClient, database: Session) -> None:
    ticket = classified(database)

    body = api.patch(
        f"/api/tickets/{ticket.id}/classification",
        json=correction(reason="Karta 8600 1234 5678 9012, tel +998 90 123 45 67"),
    ).json()

    reason = body["corrections"][0]["reason"]
    assert "8600 1234" not in reason
    assert "90 123" not in reason


@pytest.mark.parametrize(
    "body",
    [
        {"category": "nothing", "priority": "Low"},
        {"category": "other", "priority": "P1"},
        {"priority": "Low"},
        {"category": "other", "priority": "Low", "reason": "x" * 1001},
    ],
)
def test_bad_correction_is_refused(api: TestClient, database: Session, body: dict) -> None:
    ticket = classified(database)

    assert api.patch(f"/api/tickets/{ticket.id}/classification", json=body).status_code == 422


def test_meta_comes_from_the_code_and_routing_file(api: TestClient) -> None:
    body = api.get("/api/meta").json()

    assert body["categories"] == [category.value for category in Category]
    assert body["priorities"] == ["Critical", "High", "Medium", "Low"]
    assert "Security / Fraud" in body["teams"]
    assert body["routing"]["refunds"] == "Refunds"


# Search runs against the real Elasticsearch from the test stack.


@pytest.fixture
def index(database: Session) -> Iterator[SearchClient]:
    settings = get_settings()
    with httpx.Client(base_url=settings.elasticsearch_url) as raw:
        raw.delete(f"/{settings.search_index}")
        client = SearchClient(settings)
        client.ensure_index()
        yield client
        raw.delete(f"/{settings.search_index}")


def indexed(session: Session, client: SearchClient, tickets: list[Ticket]) -> None:
    """Through the outbox, as in production."""
    outbox = SearchOutboxRepository(session)
    for ticket in tickets:
        outbox.add(ticket.id, OutboxOperation.INDEX)
    session.commit()
    SearchIndexService(session, outbox, client).process_batch(100)
    settings = get_settings()
    httpx.post(f"{settings.elasticsearch_url}/{settings.search_index}/_refresh")


@pytest.mark.parametrize(
    ("text", "query"),
    [
        ("Kartam bloklandi", "karta"),
        ("Картам блокланди", "karta"),
        ("Kartam bloklandi", "карта"),
        ("O‘tkazma kelmadi", "otkazma"),
        ("Ўтказма келмади", "o'tkazma"),
        ("перевод не пришел", "perevod"),
    ],
)
def test_search_crosses_scripts_and_word_endings(
    api: TestClient, database: Session, index: SearchClient, text: str, query: str
) -> None:
    wanted = classified(database, text_masked=text)
    other = classified(database, text_masked="Boshqa mavzu")
    indexed(database, index, [wanted, other])

    body = api.get("/api/tickets", params={"q": query}).json()

    assert [item["id"] for item in body["items"]] == [str(wanted.id)]


def test_search_finds_review_tickets_too(
    api: TestClient, database: Session, index: SearchClient
) -> None:
    ticket = make_ticket(
        database,
        status=TicketStatus.NEEDS_REVIEW,
        review_reason=ReviewReason.UNCLEAR,
        text_masked="Kartam yo'q",
    )
    indexed(database, index, [ticket])

    assert api.get("/api/tickets", params={"q": "karta"}).json()["total"] == 1


def test_filters_narrow_search_results_and_total(
    api: TestClient, database: Session, index: SearchClient
) -> None:
    wanted = classified(database, channel=Channel.EMAIL, text_masked="Kartam yo'q")
    other = classified(database, text_masked="Kartam topilmadi")
    indexed(database, index, [wanted, other])

    body = api.get("/api/tickets", params={"q": "karta", "channel": "email"}).json()

    assert [item["id"] for item in body["items"]] == [str(wanted.id)]
    assert body["total"] == 1


def test_search_keeps_the_ranking(api: TestClient, database: Session, index: SearchClient) -> None:
    weak = classified(database, Priority.CRITICAL, text_masked="karta " + "boshqa so'z " * 30)
    strong = classified(database, Priority.LOW, text_masked="karta karta karta")
    indexed(database, index, [weak, strong])

    body = api.get("/api/tickets", params={"q": "karta"}).json()

    assert [item["id"] for item in body["items"]] == [str(strong.id), str(weak.id)]


def test_search_with_no_match_is_empty(
    api: TestClient, database: Session, index: SearchClient
) -> None:
    indexed(database, index, [classified(database)])

    assert api.get("/api/tickets", params={"q": "yoqsozlik"}).json() == {
        "items": [],
        "total": 0,
        "limit": 50,
        "offset": 0,
    }


def test_search_outage_is_reported_and_filters_keep_working(
    api: TestClient, database: Session
) -> None:
    classified(database)
    down = SearchClient(Settings(elasticsearch_url="http://127.0.0.1:1"))
    api.app.dependency_overrides[get_search_client] = lambda: down

    response = api.get("/api/tickets", params={"q": "karta"})

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "search_unavailable"
    assert api.get("/api/tickets").status_code == 200


def test_removed_document_is_no_longer_found(database: Session, index: SearchClient) -> None:
    ticket_id = uuid.uuid4()
    settings = get_settings()
    index.write([SearchDocument(ticket_id, "karta")])
    httpx.post(f"{settings.elasticsearch_url}/{settings.search_index}/_refresh")
    assert index.search("karta", 10) == [ticket_id]

    index.write([SearchDocument(ticket_id, None)])
    index.write([SearchDocument(ticket_id, None)])  # A second delete is not an error.
    httpx.post(f"{settings.elasticsearch_url}/{settings.search_index}/_refresh")

    assert index.search("karta", 10) == []
