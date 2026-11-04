# AI usage the hooks don't record

The hooks in this repository record Claude Code, Cursor, Codex CLI, Gemini CLI and
GitHub Copilot CLI by themselves, into the `.jsonl` files next to this one. Everything
else goes here, newest last:

- **any other AI agent** working in this repository: it adds its own entries, as
  `AGENTS.md` tells it to;
- **chat apps** (ChatGPT, Claude, Gemini, … in a browser or on a phone): you add them;
- **one of the tools above whose hook did not record a prompt**: you or the agent add it;
- **usage of Cursor, Gemini CLI and Copilot CLI sessions**: their hooks record prompts
  but not usage, so add a `Usage:` line per session (`## <date> · Cursor · <model>`
  heading, then the line below).

One entry per prompt:

```markdown
## 2026-11-05 14:30 · ChatGPT (web) · GPT-5
> The prompt, word for word. Every line starts with "> ".
> Replace secrets such as API keys with [REDACTED].
```

When a session or chat ends, add one line under its last entry:

```markdown
Usage: 41K tokens, $0.32   (what the tool shows; "unknown" if it shows nothing)
```

---
