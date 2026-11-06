# AI log

Main AI agent sessions, key prompts, cases where the agent was wrong and how that was found, and approximate token and cost usage. Exact prompts are in `ai-usage/`.

## 2026-11-06 · Claude Code · Opus 5.5 · Backend planning and documentation review

**Key prompts**

- Read the specs and dataset, then propose a backend plan without writing code.
- Review the PRD, TRD, ADRs and README against `TicketLens_Task.md` and correct them.

**Outcome**

- Profiled `data/tickets.csv` and corrected dataset facts in the TRD.
- Moved the LLM from host-only LM Studio into Docker Compose, pending the author's approval, to meet the one-command requirement.
- Rewrote `README.md` as the deliverable the assignment describes.

**Where the agent was wrong**

- In planning, the agent suggested listing LM Studio as a README prerequisite and adding a stub for clean machines. The assignment review showed this does not meet "only Docker installed", because a stub gives no real classification.
- The agent's first injection scan found 18 tickets. A sentence-level review of the dataset found 21.

**Usage:** see the session's `end` line in `ai-usage/`.

**Later correction:** the `README.md` rewrite above was reverted at the author's request. The file is read-only and matches the original template.

## 2026-11-06 · Claude Code · Opus 5.5 · Backend foundation

**Key prompt**

- Build the backend foundation: FastAPI, PostgreSQL with SQLAlchemy 2 and Alembic, configuration, health checks and Docker, with everything run inside containers.

**Outcome**

- Added the layered FastAPI app, the Alembic baseline, and Compose services for `postgres`, `elasticsearch` and `api`, plus an on-demand `tests` service.
- Verified a start from empty volumes with no `.env`, and stopped PostgreSQL and Elasticsearch for real to check `/api/health/ready`.

**Where the agent was wrong**

- Two of the first 15 tests failed because of test bugs. One password test used a value equal to the default username, and one route test read FastAPI internals that had changed. The test run in Docker exposed both.
- The agent's first report called startup verified, but the PostgreSQL healthcheck used the Unix socket and could pass during first-time init. Starting with PostgreSQL limited to 0.1 CPU crashed the API's migration once. The healthcheck now uses TCP.
- The agent's first clean-daemon run failed silently: `tar` read `C:` in the archive path as a remote host, no repository was copied, and the script kept polling for 25 minutes. Its log also showed `tests exit 0` when no tests had run. The author asked for a status check, the log showed the cause, and the script was rewritten to stop at the first failed step.

**Usage:** see the session's `end` line in `ai-usage/`.

## 2026-11-06 · Claude Code · Opus 5.5 · Ticket data model

**Key prompt**

- Implement the ticket data model, Alembic migration, repository and database tests, with no AI, routing or frontend work.

**Outcome**

- Added `users`, `import_jobs`, `tickets`, `classifications` and `corrections`, migration `0002`, and `TicketRepository`.
- Kept category, priority and team out of `tickets`, as the TRD requires: effective values come from the latest correction, else the latest AI result.

**Where the agent was wrong**

- The first `tickets` text constraint used `review_reason = 'masking_error'`. With both columns NULL it evaluated to NULL, so PostgreSQL accepted a ticket with no text and no reason. A constraint test caught it, and the check now uses `IS NOT DISTINCT FROM`.
- One index test did not expect PostgreSQL to list the `source_ticket_id` unique constraint as an index. The Docker test run exposed it.

**Usage:** see the session's `end` line in `ai-usage/`.
