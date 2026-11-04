#!/usr/bin/env node
// SessionStart / SessionEnd / UserPromptSubmit hook (.claude/settings.json):
// records what a candidate sends Claude in their copy of this repo, never
// Claude's replies, never what agents, other sessions, background tasks or
// headless runs send, as
//   ai-usage/<YYYY-MM-DD>_<session id, 8 chars>.jsonl
// with one {ts, project, branch, source, prompt} line per prompt, secrets
// masked, and an "end" line with the session's cost, tokens per model, time and
// lines changed so far (what /cost shows, its agents' included). The file is
// staged, so it goes into the candidate's next commit.
//
// Each copy records only the sessions opened in that checkout, so a candidate's
// repo holds their prompts and nobody else's, even with several candidates on
// one machine. The template itself (origin mohirdev-ai-projects/ticketlens-assignment,
// or no origin yet) records nothing: the author's sessions never ship.
//
// Everything comes from Claude Code's own transcripts, which mark where each
// prompt came from. Claude Code writes a prompt down only after this hook
// returns, so the hook only starts a detached run that waits a moment, then
// rebuilds the file of every session opened here. No node, no git: nothing is
// saved and nothing is shown.
//
// Named ai-usage.mjs, not track-prompts.mjs: Mohirdev's own track-prompts.mjs
// uploads the sessions of any checkout that commits a file by that name.
//
// `node .claude/hooks/ai-usage.mjs --self-test` checks the masking, the template
// check and how a transcript becomes a session file.
import { mkdirSync, readFileSync, readdirSync, realpathSync, writeFileSync } from "node:fs"
import { execFileSync, spawn } from "node:child_process"
import { homedir } from "node:os"
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

function sync(transcript) {
  const origin = git(REPO, "remote", "get-url", "origin")
  if (!origin || TEMPLATE.test(origin)) return // the template, or the author's copy before it is pushed
  const project = origin.split(/[/:]/).pop().replace(/\.git$/, "")
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
      const path = join(OUT, `${s.date}_${f.slice(0, 8)}.jsonl`)
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
  console.log("ai-usage self-test: ok")
}

const [mode, arg] = process.argv.slice(2)
if (mode === "--self-test") selfTest()
else if (mode === "--sync") setTimeout(() => { try { sync(arg) } catch {} }, WAIT)
else try { hook() } catch {} // never in Claude's way
