# TicketLens — Take-Home Assignment

Welcome! This repository contains everything you need for the 5-day TicketLens assignment.

## What is in this repository

| Path | What it is | Can you edit it? |
| --- | --- | --- |
| `README.md` | This file: how to set up and submit | **No** |
| `TASK.md` | The full task description and requirements | **No** |
| `data/tickets.csv` | Sample dataset (~2,000 support tickets) | **No** |
| `docs/ai-log.md` | Your AI agent usage log (template) | **Yes — you must fill it in** |
| `.claude/`, `.cursor/`, `.codex/`, `.gemini/`, `.github/hooks/` | Hooks that record your AI prompts into `ai-usage/` (script: `.claude/hooks/ai-usage.mjs`) | **No** — you may add settings, but keep the hooks |
| `ai-usage/*.jsonl` | Your prompts in Claude Code, Cursor, Codex CLI, Gemini CLI and Copilot CLI, one file per session | **No — written for you** |
| `ai-usage/manual.md` | Prompts and usage from any other AI (other agents, chat apps) | **Yes — add to it, never delete** |
| `AGENTS.md` | Instructions for AI agents, starting with the AI usage rule | **Yes — below that section** |

Everything else (code, specs, configs, tests) is yours to create.

## How to start

1. **Read `TASK.md` fully** before you write any code.

2. **Create your own copy of this repository.** Choose one:

   **Option A — GitHub template (recommended)**
   Click **"Use this template" → "Create a new repository"** at the top of this page, create it under your own account, then clone it:

   ```bash
   git clone https://github.com/<your-username>/<your-repo>.git
   cd <your-repo>
   ```

   **Option B — clone and re-point**

   ```bash
   git clone https://github.com/mohirdev-ai-projects/ticketlens-assignment.git
   cd ticketlens-assignment
   # create an EMPTY repository under your own GitHub/GitLab account first, then:
   git remote set-url origin https://github.com/<your-username>/<your-repo>.git
   git push -u origin main
   ```

3. **Send us the link to your repository** on Day 1, together with your stakeholder questions.
   If your repository is private, give read access to the reviewer account we send you.

4. Work in **your** repository only. Do not open pull requests or issues against this one.

## Rules for working in the repository

- **Do not modify** `README.md`, `TASK.md` or `data/tickets.csv`. If you need a cleaned or transformed dataset, write it to a new file.
- **Commit everything** you produce: code, docs, configs, tests, CI files, agent context files (`CLAUDE.md` / `AGENTS.md`).
- **Commit often**, with clear messages. We read the history, not only the final state.
- **Do not rewrite history**: no force-push, no squashing your commits into one at the end.
- **Keep `docs/ai-log.md` up to date.** Add an entry for every meaningful AI agent session, and commit it together with the work that session produced. Do not write the log at the end from memory.
- **Every prompt you give an AI is recorded in your repository**, in `ai-usage/`, and staged so it goes into your next commit. Do not edit, delete or disable any of it.
  - **Claude Code, Cursor, Codex CLI, Gemini CLI, GitHub Copilot CLI:** recorded automatically by the hooks in this repository (secrets masked, the AI's replies not included). Trust the hooks when your tool asks: accept the folder-trust prompt, and in Codex also run `/hooks` and trust them. Claude Code and Codex record usage too; for Cursor, Gemini CLI and Copilot CLI, add each session's usage to `ai-usage/manual.md`.
  - **Any other AI agent:** `AGENTS.md` tells it to log your prompts in `ai-usage/manual.md`. Check that it does.
  - **Chat apps** (ChatGPT, Claude, Gemini, … in a browser or on a phone) **and anything else:** add every prompt to `ai-usage/manual.md` yourself, in the format shown there, with the usage the app shows.
- **Never commit secrets.** Keep the LLM API key in a local `.env` file (it is already in `.gitignore`) and provide a `.env.example`.

## Deadlines

| When | What |
| --- | --- |
| Day 1, 18:00 | Last time for questions to the stakeholder contact |
| Day 1, 23:59 | Spec documents pushed to your repository |
| Day 7, 12:00 | Final version pushed — no commits after this time |
| Day 7, 13:00 | Presentation session |

All times are Tashkent time (UTC+05:00). Details are in `TASK.md`.

## Questions

Send questions to the stakeholder contact in writing. If something is unclear and no answer arrives in time, make a reasonable assumption and write it down in your docs.

Good luck!
