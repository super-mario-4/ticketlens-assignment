import json
import logging
import threading
import time
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app import worker
from app.classification.classifier import ClassifierReply
from app.classification.routing import RoutingConfigError, load_routing_table
from app.core.config import Settings
from app.db.session import get_session_factory
from app.models import Classification, ImportJob, Ticket, User
from app.models.enums import TicketStatus
from app.worker import run_slot, run_stale_check
from tests.factories import make_import_job, make_ticket

ANSWER = json.dumps(
    {"category": "refunds", "priority": "Low", "confidence": 0.9, "summary": "Qisqa xulosa."}
)
SETTINGS = Settings(worker_poll_seconds=0.01)
ROUTING = load_routing_table("config/routing.yaml")


class CountingClassifier:
    def __init__(self, delay: float = 0) -> None:
        self.delay = delay
        self.calls = 0
        self.lock = threading.Lock()

    def is_ready(self) -> bool:
        return True

    def complete(self, messages: Any, response_schema: Any) -> ClassifierReply:
        time.sleep(self.delay)
        with self.lock:
            self.calls += 1
        return ClassifierReply(
            content=ANSWER, model="fake", latency_ms=1, input_tokens=1, output_tokens=1
        )


def wait_for(condition: Any, seconds: float = 10) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if condition():
            return
        time.sleep(0.01)
    raise AssertionError("Condition was not met in time")


@pytest.fixture
def committed(migrated_database: None) -> Iterator[Session]:
    with get_session_factory()() as session:
        yield session

    with get_session_factory()() as cleanup:
        for model in (Ticket, ImportJob, User):
            cleanup.execute(delete(model))
        cleanup.commit()


def add_pending(session: Session, count: int) -> None:
    job = make_import_job(session)
    for _ in range(count):
        make_ticket(session, import_job=job)
    session.commit()


def status_count(status: TicketStatus) -> int:
    with get_session_factory()() as session:
        return session.scalar(
            select(func.count()).select_from(Ticket).where(Ticket.status == status)
        )


def test_slot_works_through_the_queue_and_stops(committed: Session) -> None:
    add_pending(committed, 3)
    stop = threading.Event()
    classifier = CountingClassifier()
    thread = threading.Thread(target=run_slot, args=(stop, classifier, ROUTING, SETTINGS))

    thread.start()
    wait_for(lambda: status_count(TicketStatus.CLASSIFIED) == 3)
    stop.set()
    thread.join(timeout=5)

    assert not thread.is_alive()
    assert classifier.calls == 3


def test_parallel_slots_never_classify_a_ticket_twice(committed: Session) -> None:
    add_pending(committed, 12)
    stop = threading.Event()
    classifier = CountingClassifier(delay=0.01)
    threads = [
        threading.Thread(target=run_slot, args=(stop, classifier, ROUTING, SETTINGS))
        for _ in range(3)
    ]

    for thread in threads:
        thread.start()
    wait_for(lambda: status_count(TicketStatus.CLASSIFIED) == 12)
    stop.set()
    for thread in threads:
        thread.join(timeout=5)

    assert classifier.calls == 12
    with get_session_factory()() as session:
        assert session.scalar(select(func.count()).select_from(Classification)) == 12


def test_slot_stops_when_the_queue_is_empty(committed: Session) -> None:
    stop = threading.Event()
    thread = threading.Thread(target=run_slot, args=(stop, CountingClassifier(), ROUTING, SETTINGS))

    thread.start()
    stop.set()
    thread.join(timeout=5)

    assert not thread.is_alive()


def test_database_outage_does_not_end_the_slot(monkeypatch: pytest.MonkeyPatch) -> None:
    stop = threading.Event()
    calls: list[int] = []

    def outage() -> None:
        calls.append(1)
        if len(calls) >= 3:
            stop.set()
        raise OperationalError("connect", {}, Exception("down"))

    monkeypatch.setattr(worker, "get_session_factory", outage)

    run_slot(stop, CountingClassifier(), ROUTING, SETTINGS)

    assert len(calls) == 3


class ChangingClassifier(CountingClassifier):
    """Not ready on the first checks, ready after that, and stops the worker at the end."""

    def __init__(self, stop: threading.Event, answers: list[bool]) -> None:
        super().__init__()
        self.stop = stop
        self.answers = answers

    def is_ready(self) -> bool:
        ready = self.answers.pop(0)
        if not self.answers:
            self.stop.set()
        return ready


def test_waiting_for_the_model_is_logged_once(
    committed: Session, caplog: pytest.LogCaptureFixture
) -> None:
    stop = threading.Event()
    classifier = ChangingClassifier(stop, [False, False, False, True])

    with caplog.at_level(logging.INFO, logger="app.worker"):
        run_slot(stop, classifier, ROUTING, SETTINGS)

    assert [record.getMessage() for record in caplog.records] == [
        "Model not ready, waiting",
        "Model is ready",
    ]


def test_a_ready_model_logs_nothing(committed: Session, caplog: pytest.LogCaptureFixture) -> None:
    stop = threading.Event()
    classifier = ChangingClassifier(stop, [True, True])

    with caplog.at_level(logging.INFO, logger="app.worker"):
        run_slot(stop, classifier, ROUTING, SETTINGS)

    assert caplog.records == []


def test_stale_check_returns_abandoned_tickets(committed: Session) -> None:
    make_ticket(
        committed,
        status=TicketStatus.PROCESSING,
        processing_started_at=datetime.now(UTC) - timedelta(minutes=6),
    )
    committed.commit()
    stop = threading.Event()
    thread = threading.Thread(
        target=run_stale_check, args=(stop, CountingClassifier(), ROUTING, SETTINGS)
    )

    thread.start()
    wait_for(lambda: status_count(TicketStatus.PENDING) == 1)
    stop.set()
    thread.join(timeout=5)

    assert not thread.is_alive()


def test_worker_refuses_to_start_with_a_broken_routing_file(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        worker, "get_settings", lambda: Settings(routing_config_path="/missing.yaml")
    )

    with pytest.raises(RoutingConfigError):
        worker.main()
