# Learning note: Elasticsearch

> **Draft by the AI agent, for the author to rewrite.** The assignment asks how *you* learned the technology and what surprised *you*. This draft holds only what happened in this project. The personal parts below are marked and left for the author, because the agent cannot state them on the author's behalf.

## The technology chosen

Elasticsearch, from the list in section 5 of the assignment, used for full-text search over masked tickets.

**Author to confirm:** that Elasticsearch has not been used in production before.

Tickets are written in Uzbek Latin, Uzbek Cyrillic, Russian and Russian in Latin letters, with several apostrophe forms. An operator who searches for "karta" should also find "карта" and "kartam". SQL `ILIKE` cannot do that. PostgreSQL stays the source of truth, and Elasticsearch only returns ranked ticket IDs (ADR-0002).

## How I learned it

**Author to write:** what you read, tried and asked.

What was built, in the order it was needed:

1. Ran a single node in Compose with a 512 MB heap and security turned off for local use.
2. Reused `fold_text`, the function that already folded scripts for injection matching, so the same text form is indexed and searched.
3. Wrote an index with a custom analyzer: the standard tokenizer, then lowercase, then an `edge_ngram` filter from 2 to 20 characters. Asked `_analyze` what it stores for "kartam" to confirm it: `ka`, `kar`, `kart` and so on.
4. Added an outbox table, so a ticket is saved even if Elasticsearch is down, and a worker loop that sends tasks through the `_bulk` API.
5. Sent search results back through PostgreSQL for filters and paging, keeping the relevance order with `array_position`.
6. Tested against a real node, not mocks, including the whole dataset for leaked card numbers.

## What surprised me

**Author to write:** what surprised you personally. These facts came up during the work and may help:

- The analyzer used to index and the one used to search must differ. Word beginnings belong in the index only: with `edge_ngram` at search time too, a query is split into its beginnings as well, and "karta" matches anything starting with "ka".
- A `_bulk` request returns HTTP 200 even when items inside it fail. Each item has its own status, so the client must read them. Deleting a document that is already gone counts as a 404 item, which here is not an error.
- A new document is not searchable until the next refresh, so tests must call `_refresh` before searching.
- One node with the default of one replica can never be green, because a replica cannot sit on the same node as its primary. Setting `number_of_replicas` to 0 fixes this for a single node.
- With a 512 MB heap, the container used about 420–640 MB in `docker stats`. That matters here: the model leaves very little memory for anything else (TRD section 13).
- The search index is much smaller than expected: 2,000 tickets took 476 KB after indexing, even with word beginnings stored.
