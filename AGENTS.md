# AGENTS.md

## AI usage logging (required by the assignment, do not change this section)

Every prompt the user gives an AI tool in this repository must be recorded in `ai-usage/`.

- **Claude Code, Cursor, Codex CLI, Gemini CLI and GitHub Copilot CLI** record prompts
  through hooks (`.claude/`, `.cursor/`, `.codex/`, `.gemini/`, `.github/hooks/`) into
  `ai-usage/<date>_<tool>_<session>.jsonl`. If you are one of these and such a file for
  your tool already holds the user's latest message, do nothing more.
- **Any other AI agent, or one of the above whose file does not hold that message:**
  before you act on each message from the user, append an entry for it to
  `ai-usage/manual.md` in the format shown there (the message word for word, every line
  prefixed with `> `, secrets replaced with `[REDACTED]`). When the session ends, add a
  `Usage:` line with the tokens or cost your tool reports, or `unknown`. Then run
  `git add ai-usage/manual.md`.
- Never edit or delete existing entries or files in `ai-usage/`.

<!-- Your own instructions for agents go below this line. -->
