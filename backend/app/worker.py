import logging
import signal
import threading

from sqlalchemy.exc import SQLAlchemyError

from app.classification.classifier import Classifier
from app.classification.llm import LLMClassifier
from app.classification.routing import RoutingTable, load_routing_table
from app.core.config import Settings, get_settings
from app.db.session import get_session_factory
from app.repositories.search_outbox import SearchOutboxRepository
from app.repositories.tickets import TicketRepository
from app.search.client import SearchClient
from app.services.classification import ClassificationService
from app.services.retention import RetentionService
from app.services.search_index import SearchIndexService

logger = logging.getLogger(__name__)

STALE_CHECK_INTERVAL_SECONDS = 60


def run_slot(
    stop: threading.Event, classifier: Classifier, routing: RoutingTable, settings: Settings
) -> None:
    """Handles one ticket at a time. Each slot has its own session, and `SKIP LOCKED` keeps
    slots from taking the same ticket."""
    waiting_for_model = False
    while not stop.is_set():
        claimed = 0
        try:
            with get_session_factory()() as session:
                service = ClassificationService(
                    session, TicketRepository(session), classifier, routing, settings
                )
                summary = service.process_pending(limit=1)
            claimed = summary.claimed
            # Logged on each change only: a first download can take hours.
            if summary.classifier_ready == waiting_for_model:
                waiting_for_model = not summary.classifier_ready
                logger.info("Model %s", "not ready, waiting" if waiting_for_model else "is ready")
        except SQLAlchemyError as exc:
            logger.warning("Worker could not reach the database: %s", type(exc).__name__)
        if not claimed:
            stop.wait(settings.worker_poll_seconds)


def run_stale_check(
    stop: threading.Event, classifier: Classifier, routing: RoutingTable, settings: Settings
) -> None:
    while not stop.is_set():
        try:
            with get_session_factory()() as session:
                service = ClassificationService(
                    session, TicketRepository(session), classifier, routing, settings
                )
                requeued = service.requeue_stale()
            if requeued:
                logger.warning("Returned %d stale tickets to the queue", requeued)
        except SQLAlchemyError as exc:
            logger.warning("Stale ticket check failed: %s", type(exc).__name__)
        stop.wait(STALE_CHECK_INTERVAL_SECONDS)


def run_search_index(stop: threading.Event, search: SearchClient, settings: Settings) -> None:
    """Runs without the model: tickets become searchable while it downloads (TRD section 13)."""
    while not stop.is_set():
        finished = 0
        try:
            with get_session_factory()() as session:
                service = SearchIndexService(session, SearchOutboxRepository(session), search)
                finished = service.process_batch(settings.outbox_batch_size)
        except SQLAlchemyError as exc:
            logger.warning("Search index task failed: %s", type(exc).__name__)
        if not finished:
            stop.wait(settings.outbox_poll_seconds)


def run_retention(stop: threading.Event, settings: Settings) -> None:
    while not stop.is_set():
        try:
            with get_session_factory()() as session:
                RetentionService(
                    session, TicketRepository(session), SearchOutboxRepository(session), settings
                ).clean()
        except SQLAlchemyError as exc:
            logger.warning("Retention cleanup failed: %s", type(exc).__name__)
        stop.wait(settings.retention_check_seconds)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)

    settings = get_settings()
    routing = load_routing_table(settings.routing_config_path)
    classifier = LLMClassifier(settings)
    search = SearchClient(settings)

    stop = threading.Event()
    for signal_number in (signal.SIGINT, signal.SIGTERM):
        signal.signal(signal_number, lambda *_: stop.set())

    arguments = (stop, classifier, routing, settings)
    threads = [
        threading.Thread(target=run_slot, args=arguments)
        for _ in range(settings.worker_concurrency)
    ]
    threads.append(threading.Thread(target=run_stale_check, args=arguments))
    threads.append(threading.Thread(target=run_search_index, args=(stop, search, settings)))
    threads.append(threading.Thread(target=run_retention, args=(stop, settings)))
    for thread in threads:
        thread.start()
    logger.info("Worker started with %d slots", settings.worker_concurrency)

    for thread in threads:
        thread.join()
    logger.info("Worker stopped")


if __name__ == "__main__":
    main()
