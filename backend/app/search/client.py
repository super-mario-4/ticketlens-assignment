import json
import uuid
from dataclasses import dataclass

import httpx

from app.core.config import Settings
from app.preprocess.normalize import fold_text

# Words are stored by their beginnings, so a search for "karta" also finds "kartam". Text is
# folded before it gets here, so Latin and Cyrillic spellings meet (TRD section 3).
_INDEX_BODY = {
    "settings": {
        "number_of_replicas": 0,
        "analysis": {
            "filter": {"word_start": {"type": "edge_ngram", "min_gram": 2, "max_gram": 20}},
            "analyzer": {
                "word_starts": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "word_start"],
                }
            },
        },
    },
    "mappings": {
        "dynamic": "strict",
        "properties": {
            "text_norm": {
                "type": "text",
                "analyzer": "word_starts",
                "search_analyzer": "standard",
            }
        },
    },
}


class SearchError(Exception):
    """Elasticsearch could not do the work. Tickets and filters do not depend on it."""


@dataclass(frozen=True)
class SearchDocument:
    ticket_id: uuid.UUID
    text_masked: str | None  # None removes the document.


class SearchClient:
    """Talks to Elasticsearch over HTTP. Only masked text is ever sent here."""

    def __init__(self, settings: Settings, client: httpx.Client | None = None) -> None:
        self._index = settings.search_index
        self._client = client or httpx.Client(
            base_url=settings.elasticsearch_url, timeout=settings.search_timeout_seconds
        )

    def ensure_index(self) -> None:
        try:
            if self._client.head(f"/{self._index}").status_code == httpx.codes.OK:
                return
            response = self._client.put(f"/{self._index}", json=_INDEX_BODY)
            already_exists = (
                response.status_code == httpx.codes.BAD_REQUEST
                and "resource_already_exists" in response.text
            )
            if not already_exists:
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise SearchError(type(exc).__name__) from None

    def write(self, documents: list[SearchDocument]) -> None:
        lines: list[str] = []
        for document in documents:
            action = "delete" if document.text_masked is None else "index"
            lines.append(json.dumps({action: {"_id": str(document.ticket_id)}}))
            if document.text_masked is not None:
                lines.append(json.dumps({"text_norm": fold_text(document.text_masked)}))
        try:
            response = self._client.post(
                f"/{self._index}/_bulk",
                content="\n".join(lines) + "\n",
                headers={"Content-Type": "application/x-ndjson"},
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise SearchError(type(exc).__name__) from None

        for item in response.json()["items"]:
            result = next(iter(item.values()))
            # Removing a document that is already gone is not a failure.
            if result["status"] >= 400 and result["status"] != httpx.codes.NOT_FOUND:
                raise SearchError("bulk_item_failed")

    def search(self, query: str, limit: int) -> list[uuid.UUID]:
        """Ticket IDs, best match first."""
        body = {
            "size": limit,
            "_source": False,
            "query": {"match": {"text_norm": {"query": fold_text(query), "operator": "and"}}},
        }
        try:
            response = self._client.post(f"/{self._index}/_search", json=body)
            if response.status_code == httpx.codes.NOT_FOUND:
                return []  # Nothing has been indexed yet.
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise SearchError(type(exc).__name__) from None
        return [uuid.UUID(hit["_id"]) for hit in response.json()["hits"]["hits"]]
