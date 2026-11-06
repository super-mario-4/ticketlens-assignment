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
