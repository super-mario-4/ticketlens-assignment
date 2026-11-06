from time import perf_counter
from typing import Any

import httpx

from app.classification.classifier import ClassifierReply
from app.core.config import Settings


class LLMClassifier:
    """Calls the OpenAI-compatible chat API (ADR-0001, TRD section 7.2). The address and model
    come from settings. Errors are left to the workflow, which owns the retry rules."""

    def __init__(self, settings: Settings, client: httpx.Client | None = None) -> None:
        self._settings = settings
        self._client = client or httpx.Client(
            base_url=f"{settings.llm_base_url.rstrip('/')}/",
            timeout=settings.llm_timeout,
        )

    def is_ready(self) -> bool:
        """True once the model is available. While it downloads it is not listed yet."""
        response = self._client.get("models", timeout=self._settings.health_check_timeout_seconds)
        response.raise_for_status()
        # Ollama sends `null`, not an empty list, until a model is installed.
        models = response.json()["data"] or []
        return any(model["id"] == self._settings.llm_model for model in models)

    def complete(
        self, messages: list[dict[str, str]], response_schema: dict[str, Any]
    ) -> ClassifierReply:
        started = perf_counter()
        response = self._client.post(
            "chat/completions",
            json={
                "model": self._settings.llm_model,
                "messages": messages,
                "temperature": 0,
                "max_tokens": self._settings.llm_max_tokens,
                # Thinking multiplies output tokens and time (TRD section 7.1).
                "reasoning_effort": self._settings.llm_reasoning_effort,
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "ticket_classification",
                        "strict": True,
                        "schema": response_schema,
                    },
                },
            },
        )
        latency_ms = round((perf_counter() - started) * 1000)
        response.raise_for_status()

        body = response.json()
        return ClassifierReply(
            content=body["choices"][0]["message"]["content"],
            model=self._settings.llm_model,
            latency_ms=latency_ms,
            input_tokens=body["usage"]["prompt_tokens"],
            output_tokens=body["usage"]["completion_tokens"],
        )
