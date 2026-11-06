import threading
import uuid
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from app import worker
from app.core.config import Settings, get_settings
from app.db.session import get_session_factory
from app.models import ImportJob, SearchIndexOutbox, Ticket, User
from app.models.enums import OutboxOperation, OutboxStatus, TicketStatus
from app.preprocess.mask import contains_sensitive_data
from app.repositories.search_outbox import SearchOutboxRepository
from app.repositories.tickets import TicketRepository
from app.search.client import SearchClient, SearchDocument, SearchError
from app.services.retention import RetentionService
from app.services.search_index import SearchIndexService
from tests.auth import authorized_app
from tests.factories import make_ticket

DATASET = Path("/data/tickets.csv")


class RecordingClient:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.documents: list[SearchDocument] = []

    def ensure_index(self) -> None:
        pass

    def write(self, documents: list[SearchDocument]) -> None:
        if self.fail:
            raise SearchError("ConnectError")
        self.documents.extend(documents)


@pytest.fixture
def database(migrated_database: None) -> Iterator[Session]:
    with get_session_factory()() as session:
        yield session

    with get_session_factory()() as cleanup:
        for model in (Ticket, ImportJob, User, SearchIndexOutbox):
            cleanup.execute(delete(model))
        cleanup.commit()


def service(session: Session, client: object) -> SearchIndexService:
    return SearchIndexService(session, SearchOutboxRepository(session), client)  # type: ignore[arg-type]


def task(session: Session) -> SearchIndexOutbox:
    return session.scalars(select(SearchIndexOutbox)).one()


def queued(session: Session, operation: OutboxOperation = OutboxOperation.INDEX) -> Ticket:
    ticket = make_ticket(session)
    SearchOutboxRepository(session).add(ticket.id, operation)
    session.commit()
    return ticket


def test_task_sends_the_masked_text(database: Session) -> None:
    ticket = queued(database)
    client = RecordingClient()

    finished = service(database, client).process_batch(10)

    assert finished == 1
    assert client.documents == [SearchDocument(ticket.id, "Pulim yetib bormadi")]
    assert task(database).status is OutboxStatus.DONE
    assert task(database).processed_at is not None


def test_empty_outbox_does_nothing(database: Session) -> None:
    client = RecordingClient()

    assert service(database, client).process_batch(10) == 0
    assert client.documents == []


def test_batch_size_is_respected(database: Session) -> None:
    for _ in range(3):
        queued(database)

    assert service(database, RecordingClient()).process_batch(2) == 2


def test_failure_keeps_the_task_for_a_retry(database: Session) -> None:
    ticket = queued(database)

    assert service(database, RecordingClient(fail=True)).process_batch(10) == 0

    stored = task(database)
    assert stored.status is OutboxStatus.FAILED
    assert stored.attempts == 1
    assert stored.last_error == "ConnectError"

    client = RecordingClient()
    assert service(database, client).process_batch(10) == 1
    assert client.documents[0].ticket_id == ticket.id
    database.refresh(stored)
    assert stored.status is OutboxStatus.DONE
    assert stored.attempts == 2
    assert stored.last_error is None


def test_delete_task_outlives_its_ticket(database: Session) -> None:
    ticket = queued(database, OutboxOperation.DELETE)
    ticket_id = ticket.id
    database.delete(ticket)
    database.commit()
    client = RecordingClient()

    service(database, client).process_batch(10)

    assert client.documents == [SearchDocument(ticket_id, None)]


def test_retention_removes_only_expired_tickets_and_queues_their_documents(
    database: Session,
) -> None:
    expired = make_ticket(database)
    kept = make_ticket(database)
    database.commit()
    expired_id, kept_id = expired.id, kept.id
    database.execute(
        update(Ticket)
        .where(Ticket.id == expired_id)
        .values(ingested_at=datetime.now(UTC) - timedelta(days=91))
    )
    database.commit()

    removed = RetentionService(
        database, TicketRepository(database), SearchOutboxRepository(database), Settings()
    ).clean()

    assert removed == 1
    database.expire_all()
    assert database.get(Ticket, expired_id) is None
    assert database.get(Ticket, kept_id) is not None
    stored = task(database)
    assert (stored.ticket_id, stored.operation) == (expired_id, OutboxOperation.DELETE)


def test_ticket_inside_the_window_is_kept(database: Session) -> None:
    ticket = make_ticket(database)
    database.execute(
        update(Ticket)
        .where(Ticket.id == ticket.id)
        .values(ingested_at=datetime.now(UTC) - timedelta(days=89))
    )
    database.commit()

    removed = RetentionService(
        database, TicketRepository(database), SearchOutboxRepository(database), Settings()
    ).clean()

    assert removed == 0


def test_finished_tasks_older_than_retention_are_removed(database: Session) -> None:
    queued(database)
    service(database, RecordingClient()).process_batch(10)
    database.execute(
        update(SearchIndexOutbox).values(processed_at=datetime.now(UTC) - timedelta(days=91))
    )
    database.commit()

    RetentionService(
        database, TicketRepository(database), SearchOutboxRepository(database), Settings()
    ).clean()

    assert database.scalar(select(func.count()).select_from(SearchIndexOutbox)) == 0


def test_index_worker_loop_works_without_the_model(database: Session) -> None:
    queued(database)
    stop = threading.Event()
    client = RecordingClient()
    settings = Settings(outbox_poll_seconds=0.01)
    thread = threading.Thread(target=worker.run_search_index, args=(stop, client, settings))

    thread.start()
    for _ in range(500):
        if client.documents:
            break
        stop.wait(0.01)
    stop.set()
    thread.join(timeout=5)

    assert not thread.is_alive()
    assert len(client.documents) == 1


def test_retention_worker_loop_runs_and_stops(database: Session) -> None:
    stop = threading.Event()
    thread = threading.Thread(target=worker.run_retention, args=(stop, Settings()))

    thread.start()
    stop.set()
    thread.join(timeout=5)

    assert not thread.is_alive()


def test_elasticsearch_outage_raises_a_search_error() -> None:
    client = SearchClient(Settings(elasticsearch_url="http://127.0.0.1:1"))

    with pytest.raises(SearchError):
        client.ensure_index()
    with pytest.raises(SearchError):
        client.write([SearchDocument(uuid.uuid4(), "x")])
    with pytest.raises(SearchError):
        client.search("x", 1)


@pytest.mark.skipif(not DATASET.exists(), reason="The dataset is mounted in Docker")
def test_whole_dataset_reaches_the_index_masked(database: Session) -> None:
    """TRD section 12: no raw card, CVV, expiry, passport or phone in the search index."""
    settings = get_settings()
    url = f"{settings.elasticsearch_url}/{settings.search_index}"
    httpx.delete(url)
    try:
        with TestClient(authorized_app()) as api:
            response = api.post(
                "/api/imports",
                files={"file": ("tickets.csv", DATASET.read_bytes(), "text/csv")},
            )
        assert response.json()["inserted"] == 2000

        client = SearchClient(settings)
        index = service(database, client)
        while index.process_batch(200):
            pass

        httpx.post(f"{url}/_refresh")
        hits = httpx.post(f"{url}/_search", json={"size": 2000}).json()["hits"]["hits"]
        assert len(hits) == 2000
        assert not [hit for hit in hits if contains_sensitive_data(hit["_source"]["text_norm"])]
        assert (
            database.scalar(
                select(func.count())
                .select_from(Ticket)
                .where(Ticket.status == TicketStatus.PENDING)
            )
            == 1897
        )
    finally:
        httpx.delete(url)
