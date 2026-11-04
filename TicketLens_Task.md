# TicketLens — Technical Task

**Format:** 7-day take-home project
**Expected effort:** about 20–25 hours in total
**Final submission:** Day 7, 12:00 (Tashkent time)

---

## 1. Background

A fintech company in Tashkent receives about **3,000 support messages per day** through three channels: Telegram, email and a web form.

Messages arrive in:
- Uzbek (Latin script)
- Uzbek (Cyrillic script)
- Russian
- a mix of the above in one message

Today, three operators read every message by hand and forward it to the right team. The average time to first response is about **9 hours**. The Head of Support wants this **under 1 hour**.

## 2. Your role

You are the **product owner and the tech lead** for this project. You decide what to build in 7 days, build it, run it, and present it at the end.

## 3. Stakeholder requirements

Below are the requirements as the Head of Support stated them:

1. "Every ticket must be classified into a category and a priority, and sent to the right team automatically."
2. "I need a short summary of each ticket so operators don't have to read long messages."
3. "We must keep all raw messages forever, including card numbers, for audits."
4. "It should never go down. 99.99% uptime."
5. "Use the best AI model available. Cost is not an issue."
6. "Operators need a screen to see the queue and correct wrong classifications."

You are responsible for turning these into a product. You may refine, reprioritise or challenge any of them, as long as you document your reasoning.

## 4. What we provide

| Item | Details |
| --- | --- |
| `tickets.csv` | About 2,000 sample tickets with columns: `id`, `channel`, `created_at`, `text`, `customer_id` |
|  |

## 5. Hard requirements

1. **AI coding agents.** Use AI coding agents (Claude Code, Codex, Cursor or similar) for most of the development work, and keep a log of how you used them (see section 8).
2. **Backend.** Python; FastAPI preferred.
3. **New technology.** Use at least one technology from this list that you have **not** used in production before, and state which one:
   - ClickHouse
   - Elasticsearch
   - Temporal
   - Qdrant
   - k3s + Helm
4. **One-command start.** The whole system starts with one command (`docker compose up`, `make up` or similar) on a clean Linux machine with only Docker installed.
5. **CI.** A pipeline (GitHub Actions or GitLab CI) runs tests and builds images on every push.
6. **Spec first.** Write the product and technical spec before the main implementation and send it by the end of Day 1.

## 6. What you decide

Everything not listed above is your decision, including:
- architecture and components
- which models to use and where they run
- categories, priorities and routing logic
- what is in scope for 7 days and what is not
- how you measure whether the system works

A smaller system with clear reasoning is better than a large one that is hard to explain.


## 7. Deliverables

Share one Git repository containing:

| Path | Contents |
| --- | --- |
| `docs/PRD.md` | Problem, users, success metrics, in scope / out of scope, how you handled each stakeholder requirement |
| `docs/TRD.md` | Architecture diagram, data flow, model choice, cost estimate per 1,000 tickets, failure modes |
| `docs/adr/` | At least 3 architecture decision records |
| `docs/learning-note.md` | The new technology you chose, how you learned it, what surprised you |
| `docs/ai-log.md` | Main AI agent sessions, key prompts, cases where the agent was wrong and how you found out, approximate token / cost usage |
| `CLAUDE.md` or `AGENTS.md` | The context / instruction file your agents used |
| Source code + tests | Including a small quality evaluation of classification on at least 50 tickets you labelled yourself |
| CI config | Passing on the final commit |
| `README.md` | How to run, known limitations, what you would do with 2 more weeks |

Please commit regularly; keep the full git history.

## 8. Presentation session 

About 45 minutes with the team. Be ready to:
- clone and start the system on a clean machine
- show a ticket going through the system end to end
- walk through your product and technical decisions
- make a small change to the system live, using your AI tools
- answer questions about any part of the code and docs

## 9. Rules

- Any AI tool, library or documentation is allowed.
- The work must be yours: no other person may write code or documents for you.
- You keep the code. It will not be used in any MohirDev product.

## 10. Questions

Send all questions to the stakeholder contact in writing. If something is unclear and no answer arrives in time, make a reasonable assumption and write it down in your docs.

Good luck!
