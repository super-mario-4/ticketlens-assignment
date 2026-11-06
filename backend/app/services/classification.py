import logging
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.classification.classifier import Classifier, ClassifierReply
from app.classification.prompt import PROMPT_VERSION, build_messages
from app.classification.routing import RoutingTable, decide
from app.classification.schema import ClassificationOutput
from app.core.config import Settings
from app.models import Classification, Ticket
from app.models.enums import ReviewReason, TicketStatus
from app.repositories.tickets import TicketRepository

logger = logging.getLogger(__name__)

# TRD section 11: one retry after a bad answer, two attempts when the model does not answer.
MAX_BAD_ANSWERS = 2
MAX_NO_ANSWERS = 2


@dataclass(frozen=True)
class Answer:
    reply: ClassifierReply
    output: ClassificationOutput


@dataclass
class ProcessingSummary:
    claimed: int = 0
    classified: int = 0
    needs_review: int = 0
    failed: int = 0
    classifier_ready: bool = True


class ClassificationService:
    """Moves tickets through `pending`, `processing`, then `classified` or `needs_review`.

    Only `pending` tickets are claimed, so tickets held for review at import, such as suspected
    injections, never reach a model. Model calls run outside any transaction."""

    def __init__(
        self,
        session: Session,
        tickets: TicketRepository,
        classifier: Classifier,
        routing: RoutingTable,
        settings: Settings,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._session = session
        self._tickets = tickets
        self._classifier = classifier
        self._routing = routing
        self._settings = settings
        self._sleep = sleep

    def process_pending(self, limit: int) -> ProcessingSummary:
        summary = ProcessingSummary()
        if not self._classifier_is_ready():
            summary.classifier_ready = False
            return summary

        tickets = self._tickets.claim_pending(limit, datetime.now(UTC))
        self._session.commit()
        summary.claimed = len(tickets)

        for ticket in tickets:
            self._process(ticket, summary)
        return summary

    def requeue_stale(self) -> int:
        """Returns tickets abandoned by a stopped worker to the queue (TRD section 11)."""
        timeout = timedelta(seconds=self._settings.processing_timeout_seconds)
        requeued = self._tickets.requeue_stale(datetime.now(UTC) - timeout)
        self._session.commit()
        return requeued

    def _classifier_is_ready(self) -> bool:
        try:
            return self._classifier.is_ready()
        except Exception as exc:
            logger.warning("Classifier readiness check failed: %s", type(exc).__name__)
            return False

    def _process(self, ticket: Ticket, summary: ProcessingSummary) -> None:
        ticket_id = ticket.id
        result = self.classify(ticket_id, ticket.text_masked or "")
        try:
            if isinstance(result, ReviewReason):
                self._send_to_review(ticket, result)
            else:
                self._save_answer(ticket, result)
            status = ticket.status
            self._session.commit()
        except SQLAlchemyError as exc:
            # The ticket stays in `processing`, and `requeue_stale` returns it to the queue.
            self._session.rollback()
            logger.warning("Ticket %s was not saved: %s", ticket_id, type(exc).__name__)
            summary.failed += 1
            return

        if status is TicketStatus.CLASSIFIED:
            summary.classified += 1
        else:
            summary.needs_review += 1

    def classify(self, ticket_id: uuid.UUID, text_masked: str) -> Answer | ReviewReason:
        messages = build_messages(text_masked)
        response_schema = ClassificationOutput.model_json_schema()
        bad_answers = 0
        no_answers = 0

        while True:
            try:
                reply = self._classifier.complete(messages, response_schema)
            except Exception as exc:
                no_answers += 1
                logger.warning(
                    "Classifier gave no answer for ticket %s: %s", ticket_id, type(exc).__name__
                )
                if no_answers >= MAX_NO_ANSWERS:
                    return ReviewReason.LLM_UNAVAILABLE
                self._sleep(self._settings.classifier_retry_delay_seconds)
                continue

            try:
                return Answer(reply, ClassificationOutput.model_validate_json(reply.content))
            except ValidationError:
                # The error itself is not logged: it quotes the model's answer.
                bad_answers += 1
                logger.warning("Classifier gave a bad answer for ticket %s", ticket_id)
                if bad_answers >= MAX_BAD_ANSWERS:
                    return ReviewReason.SCHEMA_ERROR

    def _send_to_review(self, ticket: Ticket, reason: ReviewReason) -> None:
        ticket.status = TicketStatus.NEEDS_REVIEW
        ticket.review_reason = reason
        ticket.processing_started_at = None

    def _save_answer(self, ticket: Ticket, answer: Answer) -> None:
        output = answer.output
        decision = decide(output, self._routing, self._settings.classification_confidence_threshold)
        self._tickets.add_classification(
            Classification(
                ticket_id=ticket.id,
                model=answer.reply.model,
                prompt_version=PROMPT_VERSION,
                category=output.category,
                priority=output.priority,
                confidence=output.confidence,
                summary=output.summary,
                team=decision.team,
                latency_ms=answer.reply.latency_ms,
                input_tokens=answer.reply.input_tokens,
                output_tokens=answer.reply.output_tokens,
            )
        )
        ticket.status = decision.status
        ticket.review_reason = decision.review_reason
        ticket.processing_started_at = None
        if decision.status is TicketStatus.CLASSIFIED:
            ticket.classified_at = datetime.now(UTC)
