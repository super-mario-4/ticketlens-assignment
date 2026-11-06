from typing import Any, Protocol

from pydantic import BaseModel, Field


class ClassifierReply(BaseModel):
    """A model's raw answer with the usage figures stored for each classification."""

    content: str
    model: str = Field(min_length=1, max_length=128)
    latency_ms: int = Field(ge=0)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)


class Classifier(Protocol):
    """What the workflow needs from a model runtime. No implementation exists yet, because the
    runtime in ADR-0001 is awaiting approval."""

    def is_ready(self) -> bool:
        """False while the model is still loading: pending tickets then stay pending."""

    def complete(
        self, messages: list[dict[str, str]], response_schema: dict[str, Any]
    ) -> ClassifierReply:
        """Raises any exception if the model gives no answer, for example on a timeout."""
