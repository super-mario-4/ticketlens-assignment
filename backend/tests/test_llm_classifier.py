import json
from collections.abc import Callable
from typing import Any

import httpx
import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.classification.llm import LLMClassifier
from app.classification.prompt import build_messages
from app.classification.routing import load_routing_table
from app.classification.schema import ClassificationOutput
from app.core.config import Settings
from app.models.enums import ReviewReason, TicketStatus
from app.repositories.tickets import TicketRepository
from app.services.classification import ClassificationService
from tests.factories import make_ticket

SCHEMA = ClassificationOutput.model_json_schema()
ANSWER = json.dumps(
    {
        "category": "refunds",
        "priority": "Medium",
        "confidence": 0.9,
        "summary": "Mijoz pulini qaytarishni so'ragan.",
    }
)


def chat_body(content: str | None = ANSWER) -> dict[str, Any]:
    return {
        "model": "qwen3.6:35b-a3b",
        "choices": [{"message": {"role": "assistant", "content": content}}],
        "usage": {"prompt_tokens": 950, "completion_tokens": 110},
    }


def classifier_with(
    handler: Callable[[httpx.Request], httpx.Response], **settings: Any
) -> LLMClassifier:
    configured = Settings(**settings)
    client = httpx.Client(
        base_url=f"{configured.llm_base_url}/",
        transport=httpx.MockTransport(handler),
    )
    return LLMClassifier(configured, client)


def test_default_settings_follow_adr_0001() -> None:
    settings = Settings()

    assert settings.llm_base_url == "http://llm:11434/v1"
    assert settings.llm_model == "qwen3.6:35b-a3b"
    assert settings.llm_timeout == 60.0


def test_request_follows_the_trd() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=chat_body())

    messages = build_messages("Pul yo'q")
    classifier_with(handler).complete(messages, SCHEMA)

    assert str(requests[0].url) == "http://llm:11434/v1/chat/completions"
    assert "authorization" not in requests[0].headers
    body = json.loads(requests[0].content)
    assert body["model"] == "qwen3.6:35b-a3b"
    assert body["messages"] == messages
    assert body["temperature"] == 0
    assert body["max_tokens"] == 300
    assert body["reasoning_effort"] == "none"
    assert body["response_format"]["type"] == "json_schema"
    assert body["response_format"]["json_schema"]["schema"] == SCHEMA


def test_address_and_model_come_from_settings() -> None:
    urls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        urls.append(str(request.url))
        return httpx.Response(200, json=chat_body())

    classifier = classifier_with(
        handler, llm_base_url="http://host.docker.internal:1234/v1", llm_model="other-model"
    )

    reply = classifier.complete(build_messages("x"), SCHEMA)

    assert urls == ["http://host.docker.internal:1234/v1/chat/completions"]
    assert reply.model == "other-model"


def test_default_client_uses_the_configured_timeout() -> None:
    classifier = LLMClassifier(Settings(llm_timeout=12.5))

    assert classifier._client.timeout.read == 12.5
    assert str(classifier._client.base_url) == "http://llm:11434/v1/"


def test_reply_holds_the_answer_and_usage() -> None:
    classifier = classifier_with(lambda _: httpx.Response(200, json=chat_body()))

    reply = classifier.complete(build_messages("x"), SCHEMA)

    assert reply.content == ANSWER
    assert reply.model == "qwen3.6:35b-a3b"
    assert (reply.input_tokens, reply.output_tokens) == (950, 110)
    assert reply.latency_ms >= 0


@pytest.mark.parametrize("status", [400, 404, 429, 500, 503])
def test_error_status_raises(status: int) -> None:
    classifier = classifier_with(lambda _: httpx.Response(status, json={"error": "x"}))

    with pytest.raises(httpx.HTTPStatusError):
        classifier.complete(build_messages("x"), SCHEMA)


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"choices": []},
        {"choices": [{}]},
        {"choices": [{"message": {}}], "usage": {}},
        {"choices": [{"message": {"content": "x"}}]},
        {"choices": [{"message": {"content": "x"}}], "usage": {"prompt_tokens": 1}},
    ],
)
def test_response_without_the_expected_fields_raises(body: dict[str, Any]) -> None:
    classifier = classifier_with(lambda _: httpx.Response(200, json=body))

    with pytest.raises((KeyError, IndexError)):
        classifier.complete(build_messages("x"), SCHEMA)


def test_empty_content_raises() -> None:
    classifier = classifier_with(lambda _: httpx.Response(200, json=chat_body(content=None)))

    with pytest.raises(ValidationError):
        classifier.complete(build_messages("x"), SCHEMA)


def test_response_that_is_not_json_raises() -> None:
    classifier = classifier_with(lambda _: httpx.Response(200, text="<html>"))

    with pytest.raises(ValueError):
        classifier.complete(build_messages("x"), SCHEMA)


def test_model_is_ready_once_listed() -> None:
    classifier = classifier_with(
        lambda _: httpx.Response(200, json={"data": [{"id": "qwen3.6:35b-a3b"}]})
    )

    assert classifier.is_ready() is True


@pytest.mark.parametrize("models", [None, [], [{"id": "qwen3.6:27b"}]])
def test_model_is_not_ready_until_listed(models: list[dict[str, str]] | None) -> None:
    classifier = classifier_with(lambda _: httpx.Response(200, json={"data": models}))

    assert classifier.is_ready() is False


def test_readiness_uses_the_short_timeout() -> None:
    timeouts: list[dict[str, float]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        timeouts.append(request.extensions["timeout"])
        return httpx.Response(200, json={"data": []})

    classifier_with(handler, health_check_timeout_seconds=1.5, llm_timeout=60).is_ready()

    assert timeouts[0]["read"] == 1.5


def service_with(session: Session, classifier: LLMClassifier) -> ClassificationService:
    return ClassificationService(
        session,
        TicketRepository(session),
        classifier,
        load_routing_table("config/routing.yaml"),
        Settings(),
        sleep=lambda _: None,
    )


def ready_or(respond: Callable[[httpx.Request], httpx.Response]) -> Callable:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/models"):
            return httpx.Response(200, json={"data": [{"id": "qwen3.6:35b-a3b"}]})
        return respond(request)

    return handler


def test_real_adapter_through_the_workflow(session: Session) -> None:
    ticket = make_ticket(session)
    classifier = classifier_with(ready_or(lambda _: httpx.Response(200, json=chat_body())))

    summary = service_with(session, classifier).process_pending(limit=10)

    session.refresh(ticket)
    assert summary.classified == 1
    assert ticket.status is TicketStatus.CLASSIFIED
    stored = ticket.classifications[0]
    assert stored.team == "Refunds"
    assert stored.model == "qwen3.6:35b-a3b"
    assert (stored.input_tokens, stored.output_tokens) == (950, 110)


def test_timeout_becomes_llm_unavailable(session: Session) -> None:
    ticket = make_ticket(session)
    calls: list[int] = []

    def respond(_: httpx.Request) -> httpx.Response:
        calls.append(1)
        raise httpx.ReadTimeout("timed out")

    service_with(session, classifier_with(ready_or(respond))).process_pending(limit=10)

    session.refresh(ticket)
    assert len(calls) == 2
    assert ticket.status is TicketStatus.NEEDS_REVIEW
    assert ticket.review_reason is ReviewReason.LLM_UNAVAILABLE


def test_server_error_becomes_llm_unavailable(session: Session) -> None:
    ticket = make_ticket(session)
    classifier = classifier_with(ready_or(lambda _: httpx.Response(500)))

    service_with(session, classifier).process_pending(limit=10)

    session.refresh(ticket)
    assert ticket.review_reason is ReviewReason.LLM_UNAVAILABLE


def test_cut_off_answer_becomes_schema_error(session: Session) -> None:
    ticket = make_ticket(session)
    cut_off = chat_body(content=ANSWER[:40])
    classifier = classifier_with(ready_or(lambda _: httpx.Response(200, json=cut_off)))

    service_with(session, classifier).process_pending(limit=10)

    session.refresh(ticket)
    assert ticket.review_reason is ReviewReason.SCHEMA_ERROR


def test_nothing_is_claimed_while_the_runtime_is_down(session: Session) -> None:
    ticket = make_ticket(session)

    def down(_: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("no route")

    summary = service_with(session, classifier_with(down)).process_pending(limit=10)

    session.refresh(ticket)
    assert summary.claimed == 0
    assert ticket.status is TicketStatus.PENDING
