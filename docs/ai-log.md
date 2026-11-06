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

## 2026-11-06 · Claude Code · Opus 5.5 · Ticket ingestion pipeline

**Key prompt**

- Implement CSV import with validation, duplicate handling, PII masking, prompt injection handling, job tracking, API endpoints and tests, with no LLM, routing or frontend work.

**Outcome**

- Added the `preprocess` module, `ImportService`, `POST /api/imports` and `GET /api/imports/{id}`.
- The full dataset imports with 21 injection tickets, 82 no-content tickets and no raw sensitive data in the database, responses or logs.

**Where the agent was wrong**

- The first detector found 18 of the 21 injection tickets. Comparing the count with the TRD exposed a fifth template, a Russian role change with none of the usual keywords.
- The first card pattern took the month of a following `11/27` as extra digits, which left part of the expiry date in the text. A unit test caught it; the dataset has no such case.
- The agent's `sed` fix did not apply, and its script still ran the end-to-end upload after the tests failed, which put 2,000 test tickets into the application database. The output showed both. The fix was redone, and the test data was removed.

**Usage:** see the session's `end` line in `ai-usage/`.

## 2026-11-06 · Claude Code · Opus 5.5 · Multipart CSV upload

**Key prompt**

- Change `POST /api/imports` to a multipart `UploadFile` upload with a Swagger file picker, keeping the import logic, and add tests.

**Outcome**

- Added `UploadFile` and `File`, with `python-multipart` in the image. Uploads within the limit stay in memory, and a middleware stops oversized uploads as they arrive, so raw CSVs still never reach disk.
- A headless Chromium run confirmed the Swagger file picker and a working upload through it.

**Where the agent was wrong**

- The agent ran its end-to-end check against the application database. Its script printed `rows before: 2005` and still ran unconditional `DELETE` statements, removing the imported tickets and import job history of the author, who was using the stack at the time. There was no backup. The 2,000 tickets were rebuilt from `data/tickets.csv` with new internal IDs. The job history is lost.
- The previous `test_upload_is_not_written_to_disk` was too weak: its upload stayed under the 1 MB spooling threshold and it patched the wrong function. The new tests were checked by removing each protection and seeing them fail.

**Usage:** see the session's `end` line in `ai-usage/`.

## 2026-11-06 · Claude Code · Opus 5.5 · Classification and routing

**Key prompt**

- Implement classification, persistence, routing, confidence handling, the processing workflow and tests. If ADR-0001 is still pending, build only the provider-independent parts and report blockers.

**Outcome**

- ADR-0001 is still pending, so no LLM adapter, provider or `worker` service was added.
- Added the response schema, prompt, `Classifier` interface, `config/routing.yaml`, routing decisions and `ClassificationService`. All of it was tested with a fake classifier, so it says nothing about real model quality.

**Where the agent was wrong**

- The first ticket tag escaping missed `< /ticket>` and `<ticket id="1">`, and the test written for it could not detect that. Review of the test found the gap before the stage ended.

**Usage:** see the session's `end` line in `ai-usage/`.

## 2026-11-06 · Claude Code · Opus 5.5 · LLM integration and worker

**Key prompt**

- Implement Stage 5, following ADR-0001 exactly. No document defines stages, so this was scoped from the author's note and the Stage 4 blockers: the runtime, the adapter, the worker, the LLM status in `/api/health/ready` and the reclassify endpoint.

**Outcome**

- Added the `llm` and `worker` Compose services, `LLMClassifier`, `app/worker.py` and `POST /api/tickets/{id}/reclassify`.
- ADR-0001 still says the runtime awaits approval. The author told the agent to follow it, so the code uses what its decision names.
- Checked against a real `ollama/ollama:0.40.15` container in a throwaway project with a tiny test model. The configured model is about 22.6 GB and cannot load in the 15.5 GB Docker here, so it has not been run.

**Where the agent was wrong**

- `is_ready()` crashed on every poll during the model download, because Ollama sends `"data": null` with no models and the mocks used `[]`. 505 passing tests missed it, and only the real container showed it.
- `get_classifier` created a new HTTP client on every `/api/health/ready` call and never closed it. Code review found this.
- The agent started the throwaway run after a failed test run, and its first verification runs proved nothing: a failed upload left 0 tickets, so "queue drained" passed without any work. The result looked too fast, which led to the log. The script then gained checks on row counts and on stored results.

**Usage:** see the session's `end` line in `ai-usage/`.

## 2026-11-06 · Claude Code · Opus 5.5 · CI and final verification

**Key prompt**

- Add CI, verify a clean Docker start, run all tests and the evaluation, audit the documents, and report what is incomplete without claiming unperformed work.

**Outcome**

- Added `.github/workflows/ci.yml` following TRD section 14. It passes `actionlint`, and its commands were run on an empty Docker daemon. It has not run on GitHub.
- Corrected TRD lines that no longer matched the code after the move to multipart upload, and recorded `finished_at`.
- The worker now logs when it starts and stops waiting for the model.
- Not done, and not claimed: a run of the ADR-0001 model, the 50-ticket evaluation, search, the frontend and the learning note.

**Where the agent was wrong**

- The clean-daemon run was first too slow, then failed in `pip install`, while the model download used the connection. The agent separated this from a project fault by reproducing it, then loaded prebuilt images. That run therefore does not prove a from-scratch image build.
- One script edit failed and the agent launched anyway. It stopped the run, corrected the line and confirmed it before launching again.

**Usage:** see the session's `end` line in `ai-usage/`.

## 2026-11-06 · Claude Code · Opus 5.5 · Real model, evaluation and remaining features

**Key prompt**

- Continue Stage 6 with the ADR-0001 model now running: watch the worker, test the real pipeline and its errors, do the 50-ticket evaluation, build what remains, and report only what was really done.

**Outcome**

- Ran `qwen3.6:35b-a3b` for the first time. A read-only probe with the worker's exact request came first, because a call over the 60-second timeout would have sent every ticket to `llm_unavailable`.
- The agent labelled 111 scored tickets and 15 held tickets, before seeing the model's answers on them. The labels are the agent's, not the author's, so `eval/README.md` asks the author to review them.
- Built login and roles, the ticket list, detail and correction APIs, statistics, Elasticsearch search through an outbox, retention cleanup, the web screens, `make` commands and `eval/`.
- Prompt `v1` missed the priority target at 77.5%. `v2` added the examples from the PRD and reached 82.9%, on a set already seen, so that figure is not independent.

**Where the agent was wrong**

- The first report marked a lost-card ticket as "obeyed the injection". The labels for held tickets were missing, because the command that wrote them had failed without the agent noticing, and the check treated an empty label as "not fraud". Reading the report found it. The check now has tests.
- The prompt edit left a literal line break inside two sentences, and the run started before anyone looked. The agent stopped it and printed the prompt as the model sees it before running again.
- `make bench` first reported 88 tickets an hour, because the time included the hours the worker was stopped. The real figure was about 620. The agent noticed that it disagreed with an uninterrupted window in the database.
- Two failed clean starts were first blamed on how the command was launched. The real cause was that Compose pulls every image before starting anything, which took 13 minutes 42 seconds and exceeded the agent's 10-minute limit.
- Killing live services to test failures was refused by the tool's safety check. On a throwaway project instead, the agent's extra worker slowed the shared model enough to cause 3 read timeouts on the live worker, which recovered on retry. The test then stopped when the computer ran low on memory, so recovery of a killed worker was not observed with the real model.

**Usage:** see the session's `end` line in `ai-usage/`.
