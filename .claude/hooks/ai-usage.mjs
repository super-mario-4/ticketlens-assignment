#!/usr/bin/env node
// Records what a candidate sends an AI coding tool in their copy of this repo,
// never the tool's replies, as
//   ai-usage/<YYYY-MM-DD>_<tool>_<session id, 8 chars>.jsonl
// with one {ts, project, branch, prompt, ...} line per prompt, secrets masked,
// and, where the tool keeps them, an "end" line with the session's usage so far.
// The file is staged, so it goes into the candidate's next commit. Tools no hook
// reaches are logged by hand, or by the agent itself, in ai-usage/manual.md
// (see AGENTS.md and README.md).
//
// Each copy records only its own sessions, so a candidate's repo holds their
// prompts and nobody else's, even with several candidates on one machine. The
// template itself (origin mohirdev-ai-projects/ticketlens-assignment, or no
// origin yet) records nothing: the author's sessions never ship.
//
// Claude Code (.claude/settings.json: SessionStart, SessionEnd, UserPromptSubmit):
// everything comes from its own transcripts, which mark where each prompt came
// from, so what agents, other sessions, background tasks or headless runs send
// is left out, and the end line has the cost, tokens per model, time and lines
// changed (what /cost shows, its agents' included). It writes a prompt down only
// after this hook returns, so the hook only starts a detached run that waits a
// moment, then rebuilds the file of every session opened here.
//
// Cursor (.cursor/hooks.json: beforeSubmitPrompt), Codex CLI (.codex/hooks.json:
// UserPromptSubmit, Stop), Gemini CLI (.gemini/settings.json: BeforeAgent) and
// Copilot CLI (.github/hooks/ai-usage.json: userPromptSubmitted) run it with
// --tool <name>: the prompt comes in the hook's input. Only Codex's transcript
// keeps token totals; the others record prompts and, where given, the model.
//
// No node, no git: nothing is saved and nothing is shown. A hook never blocks.
//
// Named ai-usage.mjs, not track-prompts.mjs: Mohirdev's own track-prompts.mjs
// uploads the sessions of any checkout that commits a file by that name.
//
// `node .claude/hooks/ai-usage.mjs --self-test` checks the masking, the template
// check and how each tool's input becomes a session file.
import { mkdirSync, mkdtempSync, readFileSync, readdirSync, realpathSync, rmSync, writeFileSync } from "node:fs"
import { execFileSync, spawn } from "node:child_process"
import { homedir, tmpdir } from "node:os"
import { dirname, join } from "node:path"
import { fileURLToPath } from "node:url"
import assert from "node:assert/strict"

const SELF = fileURLToPath(import.meta.url)
const REPO = dirname(dirname(dirname(SELF))) // <repo>/.claude/hooks/ai-usage.mjs
const OUT = join(REPO, "ai-usage")
const TEMPLATE = /[/:]mohirdev-ai-projects\/ticketlens-assignment(?:\.git)?\/?$/i
const WAIT = 3000 // for Claude Code to write down the prompt that fired the hook

// Over-masking is the safe direction: a prompt is read by people, a key is used.
const SECRETS = [
  [/-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----/g, "[REDACTED]"],
  [/\b(?:sk-(?:ant-)?[\w-]{16,}|gh[pousr]_\w{20,}|github_pat_\w{20,}|AKIA[0-9A-Z]{16}|xox[abprs]-[\w-]{10,}|AIza[\w-]{35}|\d{8,10}:[\w-]{35}|eyJ[\w-]{10,}\.[\w-]{10,}\.[\w-]{10,})/g, "[REDACTED]"],
  [/(bearer\s+)[\w.~+/=-]{16,}/gi, "$1[REDACTED]"],
  [/((?:password|passwd|pwd|secret|token|api[_-]?key)\s*[:=]\s*)["']?[^\s"',]+["']?/gi, "$1[REDACTED]"],
  [/(\w+:\/\/[^\s:/@]+:)[^\s@/]+@/g, "$1[REDACTED]@"],
]
const mask = (s) => SECRETS.reduce((text, [re, to]) => text.replace(re, to), s)

// What Claude Code wraps around a message no person typed: another session's,
// a teammate's, a background agent's hand-back, a finished task's. A hand-back
// can be marked as the person's, so its wrapper rules it out too.
const MACHINE = /^\s*<(?:agent-message|teammate-message|cross-session-message|task-notification)[\s>]/

const parse = (line) => {
  try { return JSON.parse(line) } catch { return null }
}

const git = (cwd, ...args) => {
  try {
    return execFileSync("git", ["-C", cwd, ...args], { encoding: "utf8", timeout: 5000, stdio: ["ignore", "pipe", "ignore"] }).trim()
  } catch { return "" }
}

const ls = (dir) => {
  try { return readdirSync(dir) } catch { return [] }
}

const real = (path) => {
  try { return realpathSync(path) } catch { return null }
}

const localDate = (d) =>
  [d.getFullYear(), d.getMonth() + 1, d.getDate()].map((n) => String(n).padStart(2, "0")).join("-")

// What the person sent, as they'd write it: a /command or skill with its
// arguments, not the tags the transcript keeps it in.
function promptText(content) {
  const text = typeof content === "string"
    ? content
    : (content ?? []).filter((b) => b.type === "text").map((b) => b.text).join("\n")
  const command = text.match(/<command-name>([^<]*)<\/command-name>/)?.[1]
  if (!command) return { text }
  const args = text.match(/<command-args>([\s\S]*?)<\/command-args>/)?.[1].trim()
  return { text: args ? `${command} ${args}` : command, command: true }
}

// A transcript as a session file, or null for a headless run (claude -p, the
// SDK) or a session no person wrote in. The person's prompts are those marked
// origin human, not the hidden ones a skill or hook adds.
function session(lines, project) {
  const records = lines.map(parse).filter(Boolean)
  const entrypoint = records.find((r) => r.entrypoint)?.entrypoint
  if (!entrypoint || entrypoint.startsWith("sdk")) return null
  const prompts = records
    .filter((r) => r.type === "user" && r.origin?.kind === "human" && !r.isMeta)
    .map((r) => ({ r, ...promptText(r.message?.content) }))
    .filter(({ text }) => text.trim() && !MACHINE.test(text))
  if (!prompts.length) return null
  const out = prompts.map(({ r, text, command }) => ({
    ts: r.timestamp,
    project,
    branch: r.gitBranch,
    source: r.promptSource ?? (command ? "command" : undefined),
    prompt: mask(text),
  }))
  // Claude Code rewrites its totals now and then and when the session closes; the last counts.
  const cost = records.findLast((r) => r.type === "cost-state")
  if (cost) {
    const { totalCostUSD, totalDuration, totalAPIDuration, totalLinesAdded, totalLinesRemoved, modelUsage } = cost
    out.push({
      type: "end",
      ts: records.findLast((r) => r.timestamp)?.timestamp,
      version: records.find((r) => r.version)?.version,
      entrypoint,
      totalCostUSD, totalDuration, totalAPIDuration, totalLinesAdded, totalLinesRemoved, modelUsage,
    })
  }
  const first = prompts[0].r
  return {
    cwd: first.cwd,
    date: localDate(new Date(first.timestamp)),
    text: out.map((line) => JSON.stringify(line) + "\n").join(""),
  }
}

function hook() {
  const h = JSON.parse(readFileSync(0, "utf8"))
  if (!h.transcript_path) return
  spawn(process.execPath, [SELF, "--sync", h.transcript_path], { detached: true, stdio: "ignore", windowsHide: true }).unref()
}

// The candidate's copy: not the template, nor the author's copy before it is pushed.
const recording = (origin) => Boolean(origin) && !TEMPLATE.test(origin)
const projectOf = (origin) => origin.split(/[/:]/).pop().replace(/\.git$/, "")

function sync(transcript) {
  const origin = git(REPO, "remote", "get-url", "origin")
  if (!recording(origin)) return
  const project = projectOf(origin)
  // Every Claude config dir here (~/.claude, ~/.claude-2, the session's own):
  // a session is recorded whichever one it ran under. Each transcript folder of
  // this checkout and its subfolders is read once, however many dirs link to it.
  const roots = [dirname(dirname(transcript)), ...ls(homedir()).filter((d) => d.startsWith(".claude")).map((d) => join(homedir(), d, "projects"))]
  const prefix = REPO.replace(/[^a-zA-Z0-9]/g, "-") // how Claude Code names a folder's transcript dir
  const dirs = [...new Set([dirname(transcript), ...roots.flatMap((r) => ls(r).filter((d) => d.startsWith(prefix)).map((d) => join(r, d)))].map(real))]
    .filter(Boolean)
  for (const dir of dirs) {
    for (const f of ls(dir).filter((f) => f.endsWith(".jsonl"))) {
      const s = session(readFileSync(join(dir, f), "utf8").split("\n"), project)
      // Opened in this checkout: not a sibling folder, a worktree or a nested repo, which record their own.
      if (!s || real(git(s.cwd, "rev-parse", "--show-toplevel")) !== REPO) continue
      const path = join(OUT, `${s.date}_claude_${f.slice(0, 8)}.jsonl`)
      let old = null
      try { old = readFileSync(path, "utf8") } catch {}
      if (old === s.text) continue
      mkdirSync(OUT, { recursive: true })
      writeFileSync(path, s.text)
    }
  }
  // ponytail: an add that loses the index lock to the candidate's own git command is retried by the next run.
  git(REPO, "add", "--", "ai-usage")
}

// Another tool's hook input. The field names differ per tool; these cover all four.
function fields(h) {
  const t = new Date(h.timestamp ?? NaN) // Gemini: ISO string, Copilot: epoch ms, the others: none
  return {
    id: String(h.session_id ?? h.sessionId ?? h.conversation_id ?? "").replace(/[^\w-]/g, "").slice(0, 8),
    ts: (Number.isNaN(t.getTime()) ? new Date() : t).toISOString(),
    model: h.model || undefined,
    prompt: typeof h.prompt === "string" && h.prompt.trim() ? h.prompt : null,
  }
}

// Codex's transcript keeps running token totals, the last one counts. The other
// tools' transcripts keep none, or aren't JSONL: null.
function tokenUsage(transcript) {
  let text = ""
  try { text = readFileSync(transcript, "utf8") } catch { return null }
  const last = text.split("\n").findLast((l) => l.includes('"token_count"'))
  return parse(last ?? "")?.payload?.info?.total_token_usage ?? null
}

// The session file with this event's prompt added and its end line replaced.
function update(text, { ts, model, prompt }, base, usage) {
  const lines = text.split("\n").map(parse).filter((r) => r && r.type !== "end")
  if (prompt) lines.push({ ts, ...base, model, prompt: mask(prompt) })
  if (usage) lines.push({ type: "end", ts, model, usage })
  return lines.map((l) => JSON.stringify(l) + "\n").join("")
}

function record(tool, h) {
  const f = fields(h)
  const origin = git(REPO, "remote", "get-url", "origin")
  if (!f.id || !recording(origin)) return
  const tag = `_${tool}_${f.id}.jsonl`
  const path = join(OUT, ls(OUT).find((n) => n.endsWith(tag)) ?? `${localDate(new Date(f.ts))}${tag}`)
  let old = ""
  try { old = readFileSync(path, "utf8") } catch {}
  const base = { project: projectOf(origin), branch: git(REPO, "rev-parse", "--abbrev-ref", "HEAD"), tool }
  const text = update(old, f, base, tokenUsage(h.transcript_path))
  if (text === old) return
  mkdirSync(OUT, { recursive: true })
  writeFileSync(path, text)
  git(REPO, "add", "--", "ai-usage")
}

// What each tool wants back. Cursor: let the prompt through. Gemini, and Codex's
// Stop: JSON only. Codex's UserPromptSubmit: nothing, its stdout becomes context.
const reply = (tool, h) =>
  tool === "cursor" ? '{"continue":true}' : tool === "gemini" || h.hook_event_name === "Stop" ? "{}" : ""

function selfTest() {
  const secrets = [
    "ghp_" + "a1".repeat(18),
    "sk-ant-api03-" + "x".repeat(40),
    "AKIA" + "ABCDEFGHIJKLMNOP",
    "123456789:" + "AAH".repeat(11) + "xx",
    "eyJhbGciOiJIUzI1.eyJzdWIiOiIxMjM0.SflKxwRJSMeKKF2QT4",
  ]
  for (const s of secrets) assert.equal(mask(`use ${s} please`), "use [REDACTED] please", s)
  assert.equal(mask("Authorization: Bearer abcdefghijklmnop123"), "Authorization: Bearer [REDACTED]")
  assert.equal(mask('DB_PASSWORD="hunter2" next'), "DB_PASSWORD=[REDACTED] next")
  assert.equal(mask("postgres://app:s3cret@db:5432/x"), "postgres://app:[REDACTED]@db:5432/x")
  const plain = "fix the task-runner bug in api/auth.py, the token check at line 40"
  assert.equal(mask(plain), plain)

  // The template records nothing; a candidate's copy, whatever it is called, does.
  for (const url of ["https://github.com/mohirdev-ai-projects/ticketlens-assignment.git", "git@github.com:Mohirdev-AI-Projects/ticketlens-assignment", "https://github.com/mohirdev-ai-projects/ticketlens-assignment/"])
    assert.equal(TEMPLATE.test(url), true, url)
  for (const url of ["https://github.com/candidate/ticketlens-assignment.git", "git@github.com:candidate/ticketlens.git", "https://github.com/mohirdev-ai-projects/ticketlens-assignment-fork.git"])
    assert.equal(TEMPLATE.test(url), false, url)

  const at = (n) => `2026-10-30T10:0${n}:00.000Z`
  const user = (n, content, extra = {}) => JSON.stringify({ type: "user", timestamp: at(n), cwd: "/nowhere/ticketlens", gitBranch: "main", entrypoint: "cli", version: "2.1.316", message: { content }, ...extra })
  const human = { origin: { kind: "human" } }
  const transcript = [
    JSON.stringify({ type: "mode" }),
    user(1, `fix the login bug, key ${secrets[1]}`, { ...human, promptSource: "typed" }),
    user(2, [{ type: "text", text: "and this one" }, { type: "image" }], { ...human, promptSource: "queued" }),
    user(3, "<command-message>grill-me</command-message>\n<command-name>/grill-me</command-name>\n<command-args>the export flow</command-args>", human),
    user(3, "Base directory for this skill: ~/.claude/skills/grill-me", { isMeta: true }),
    user(4, "<command-message>finish-it</command-message>\n<command-name>/finish-it</command-name>", human),
    user(5, "Another Claude session sent a message:\n<cross-session-message from=\"x\">do it</cross-session-message>", { origin: { kind: "peer" }, isMeta: true }),
    user(6, "<task-notification>\n<task-id>b1</task-id>", { origin: { kind: "task-notification" } }),
    user(7, '<agent-message from="a1082a36c6ec16b8d">\n[Subagent hand-back] The final report', { ...human, promptSource: "typed" }),
    user(8, [{ type: "tool_result", content: "ok" }]),
    "not json",
    JSON.stringify({ type: "cost-state", totalCostUSD: 1.25, totalDuration: 9, totalAPIDuration: 4, totalLinesAdded: 2, totalLinesRemoved: 1, modelUsage: { opus: { outputTokens: 5, costUSD: 1.25 } } }),
  ]
  const s = session(transcript, "ticketlens")
  const lines = s.text.trim().split("\n").map((l) => JSON.parse(l))
  assert.deepEqual(lines.map((l) => [l.source, l.prompt]).slice(0, -1), [
    ["typed", "fix the login bug, key [REDACTED]"],
    ["queued", "and this one"],
    ["command", "/grill-me the export flow"],
    ["command", "/finish-it"],
  ])
  assert.deepEqual(lines.at(-1), { type: "end", ts: at(8), version: "2.1.316", entrypoint: "cli", totalCostUSD: 1.25, totalDuration: 9, totalAPIDuration: 4, totalLinesAdded: 2, totalLinesRemoved: 1, modelUsage: { opus: { outputTokens: 5, costUSD: 1.25 } } })
  assert.equal(lines[0].project, "ticketlens")
  assert.equal(s.cwd, "/nowhere/ticketlens")
  assert.equal(s.date, localDate(new Date(at(1))))
  assert.equal(session(transcript.filter((l) => !l.includes("cost-state")), "x").text.includes('"type":"end"'), false) // no totals yet
  assert.equal(session(transcript.map((l) => l.replaceAll('"entrypoint":"cli"', '"entrypoint":"sdk-cli"')), "x"), null) // headless
  assert.equal(session(transcript.filter((l) => !l.includes('"kind":"human"')), "x"), null) // no person wrote in it

  // Each tool's hook input, as its docs give it.
  const inputs = {
    cursor: { conversation_id: "c0ffee12-3456", generation_id: "g1", model: "gpt-5", hook_event_name: "beforeSubmitPrompt", workspace_roots: ["/w"], user_email: "x@y.z", prompt: "add a test" },
    codex: { session_id: "01a0f1d7-65f8", turn_id: "t1", cwd: "/w", hook_event_name: "UserPromptSubmit", model: "gpt-5.5", prompt: "add a test" },
    gemini: { session_id: "9f8e7d6c-5b4a", timestamp: at(1), cwd: "/w", hook_event_name: "BeforeAgent", prompt: "add a test" },
    copilot: { sessionId: "5a5a5a5a-0000", timestamp: Date.parse(at(1)), cwd: "/w", prompt: "add a test" },
  }
  assert.deepEqual(Object.values(inputs).map((h) => fields(h).id), ["c0ffee12", "01a0f1d7", "9f8e7d6c", "5a5a5a5a"])
  assert.equal(fields(inputs.gemini).ts, at(1))
  assert.equal(fields(inputs.copilot).ts, at(1))
  assert.equal(fields(inputs.cursor).model, "gpt-5")
  assert.equal(fields({ session_id: "s", hook_event_name: "Stop" }).prompt, null)
  assert.deepEqual(Object.keys(inputs).map((tool) => reply(tool, inputs[tool])), ['{"continue":true}', "", "{}", ""])
  assert.equal(reply("codex", { hook_event_name: "Stop" }), "{}")

  // Prompts accumulate, masked; the end line is replaced, never repeated.
  const base = { project: "ticketlens", branch: "main", tool: "codex" }
  const one = update("", { ...fields(inputs.codex), prompt: `use ${secrets[0]}` }, base, { total_tokens: 10 })
  const two = update(one, fields(inputs.codex), base, { total_tokens: 25 })
  const rows = two.trim().split("\n").map((l) => JSON.parse(l))
  assert.deepEqual(rows.map((r) => r.prompt ?? r.usage.total_tokens), ["use [REDACTED]", "add a test", 25])
  assert.equal(rows[0].model, "gpt-5.5")
  assert.equal(update(two, fields({ session_id: "s" }), base, null), two.split("\n").slice(0, 2).join("\n") + "\n") // a Stop with no totals: prompts stay

  const box = mkdtempSync(join(tmpdir(), "ai-usage-"))
  const rollout = join(box, "rollout.jsonl")
  const tokens = (n) => JSON.stringify({ type: "event_msg", payload: { type: "token_count", info: { total_token_usage: { total_tokens: n } } } })
  writeFileSync(rollout, [JSON.stringify({ type: "session_meta" }), tokens(5), tokens(9), JSON.stringify({ type: "response_item" })].join("\n"))
  assert.deepEqual(tokenUsage(rollout), { total_tokens: 9 })
  writeFileSync(rollout, JSON.stringify({ messages: [] }, null, 2)) // a transcript that keeps no totals
  assert.equal(tokenUsage(rollout), null)
  assert.equal(tokenUsage(null), null)
  rmSync(box, { recursive: true, force: true })
  console.log("ai-usage self-test: ok")
}

const [mode, arg] = process.argv.slice(2)
if (mode === "--self-test") selfTest()
else if (mode === "--sync") setTimeout(() => { try { sync(arg) } catch {} }, WAIT)
else if (mode === "--tool") {
  let h = {}
  try { h = JSON.parse(readFileSync(0, "utf8")); record(arg, h) } catch {} // never in the tool's way
  process.stdout.write(reply(arg, h))
} else try { hook() } catch {} // never in Claude's way
