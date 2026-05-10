# AgentTrace for Claude Code

**Know what Claude Code changed — before you merge it.**

AgentTrace is a local CLI safety layer for Claude Code sessions. It records every command run, every file touched, and every Git change made during an AI coding session, scores the risk, and generates a Markdown report so you can review what happened before trusting the result.

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Typer](https://img.shields.io/badge/CLI-Typer-009688?style=flat-square)](https://typer.tiangolo.com/)
[![Pydantic v2](https://img.shields.io/badge/Models-Pydantic_v2-E92063?style=flat-square)](https://docs.pydantic.dev/)
[![Rich](https://img.shields.io/badge/Terminal-Rich-7B2FBE?style=flat-square)](https://rich.readthedocs.io/)
[![pytest](https://img.shields.io/badge/Tests-pytest-0A9EDC?style=flat-square)](https://pytest.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)](LICENSE)
[![Build in Public](https://img.shields.io/badge/%F0%9F%94%A8-Building_in_Public-orange?style=flat-square)]()

> **Not a token tracker. Not a dashboard. Not a cloud product.**
> AgentTrace answers one question: *what did Claude Code do to my codebase, and should I trust it?*

---

## The Problem

You give Claude Code a task. It runs for a few minutes — editing files, running shell commands, touching auth logic, modifying tests, changing configuration. Then it stops.

And you have no record of what happened.

- What commands did it actually run?
- Did it touch `.env`, secrets, or payment code?
- Did it modify your tests without telling you?
- How big is this diff really?
- Is this safe to merge?

Most existing Claude Code tools track **tokens and cost**. AgentTrace tracks **what changed in your code and whether it's safe** — a different problem entirely.

---

## What AgentTrace Does

AgentTrace acts as a **black-box recorder and safety reviewer** for Claude Code sessions.

It keeps a local, append-only log of everything that happened — stored as plain files inside your project — then gives you a risk score and a readable report before you merge anything.

```
Session recorder   →   Risk engine   →   Markdown report
```

No cloud. No database. No background process. No server to run.

---

## Current State — Phases 0–3 Complete

```bash
agenttrace init                                 # set up inside any project
agenttrace start "fix authentication bug"       # begin a named session
agenttrace event command "npm test"             # record a command that ran
agenttrace event file "src/auth/login.ts"       # record a file that was touched
agenttrace event note "rewrote token refresh"   # attach a free note
agenttrace events                               # list everything that happened
agenttrace diff                                 # show git changes and stats
agenttrace snapshot                             # save git state mid-session
agenttrace status                               # check the current session
```

---

## What's Coming

| Phase | Command | What It Adds |
|-------|---------|--------------|
| 4 🔨 | `agenttrace risk` | Score every command and file as low / medium / high risk |
| 5 📋 | `agenttrace report` | Auto-generate a full Markdown session report |
| 6 📋 | `agenttrace claude setup` | Install Claude Code hooks — no more manual logging |
| 7 📋 | `agenttrace hook ...` | Fully automatic recording while Claude Code runs |
| 11 📋 | Guard mode | Block dangerous commands before they execute |

**The end goal — one workflow, fully automatic:**

```bash
agenttrace init
agenttrace claude setup          # once
agenttrace start "fix auth bug"
claude                           # Claude Code works — AgentTrace records everything
agenttrace report                # full report: what happened, risk score, recommendation
```

---

## Install

**Requirements:** Python 3.11+, Git

```bash
git clone https://github.com/Aa083824577/AgentTrace-for-Claude-Code.git
cd AgentTrace-for-Claude-Code

# macOS / Linux
python3 -m venv .venv && source .venv/bin/activate

# Windows PowerShell
python -m venv .venv && .venv\Scripts\Activate.ps1

pip install -e ".[dev]"
agenttrace --help
```

---

## A Full Session Right Now

```bash
# Initialize once per project
agenttrace init

# Start before opening Claude Code
agenttrace start "fix authentication bug"

# After Claude Code finishes — log what it did
agenttrace event command "npm test"
agenttrace event command "npm run lint"
agenttrace event file "src/auth/login.ts"
agenttrace event file "src/auth/session.ts"
agenttrace event note "Claude rewrote token refresh logic"

# Save git state
agenttrace snapshot

# Review everything
agenttrace events
agenttrace diff
```

---

## Terminal Output

**`agenttrace status`**
```
AgentTrace Status

  Session ID    2026-05-08-155726
  Task          fix authentication bug
  Project       /Users/me/my-project
  Started At    2026-05-08T15:57:26
  Status        running
```

**`agenttrace events`**
```
AgentTrace Events

  Time                  Type      Risk       Message
  2026-05-08T16:01:22   command   unknown    npm test
  2026-05-08T16:02:10   file      unknown    src/auth/login.ts
  2026-05-08T16:03:15   note      unknown    Claude rewrote token refresh logic
```

**`agenttrace diff`**
```
Branch: main

  Changed Files
    src/auth/login.ts
    src/auth/session.ts
    tests/auth.test.ts

  Summary
    Files changed:  3
    Insertions:     120
    Deletions:      14
```

**`agenttrace risk` — Phase 4, coming next**
```
Session Risk: MEDIUM

  Reasons
    · Modified auth file: src/auth/login.ts
    · Modified auth file: src/auth/session.ts
    · Test file changed: tests/auth.test.ts
    · No dangerous shell commands detected

  Recommendation
    Review carefully before merging.
```

**`agenttrace report` — Phase 5**
```
Report saved to:
  .agenttrace/sessions/2026-05-08-155726/report.md
```

---

## How Data Is Stored

Everything lives inside `.agenttrace/` in your project. Readable without any tools.

```
.agenttrace/
  current_session.json          ← pointer to the active session
  sessions/
    2026-05-08-155726/
      session.json              ← session metadata
      events.jsonl              ← append-only event log
      snapshot.json             ← git state at snapshot time
      report.md                 ← generated report (Phase 5)
```

Events are plain JSONL — one JSON object per line:

```jsonl
{"id":"evt_20260508_160122_a1b2","type":"command","time":"2026-05-08T16:01:22","message":"npm test","payload":{"command":"npm test"},"risk":"unknown"}
{"id":"evt_20260508_160210_c3d4","type":"file","time":"2026-05-08T16:02:10","message":"src/auth/login.ts","payload":{"path":"src/auth/login.ts"},"risk":"unknown"}
{"id":"evt_20260508_160305_e5f6","type":"note","time":"2026-05-08T16:03:15","message":"Claude rewrote token refresh logic","payload":{},"risk":"unknown"}
```

JSONL was chosen deliberately: append-only, no parser needed, readable with `cat`.

---

## Built With

Every dependency has a reason to be here.

| Tool | Why |
|------|-----|
| **[Python 3.11+](https://www.python.org/)** | Core language — type hints, match statements, modern stdlib |
| **[Typer](https://typer.tiangolo.com/)** | CLI framework — commands defined from Python type annotations, zero boilerplate |
| **[Rich](https://rich.readthedocs.io/)** | Terminal output — tables, panels, colors without touching ANSI codes |
| **[Pydantic v2](https://docs.pydantic.dev/)** | Data models — `Session`, `Event`, `GitSummary` with built-in validation and serialization |
| **[PyYAML](https://pyyaml.org/)** | Risk rules — `.agenttrace/rules.yaml` for per-project customization in Phase 4 |
| **[pytest](https://pytest.org/)** | Tests — `CliRunner` for CLI tests, isolated temp filesystems per test |
| **subprocess + Git** | Git integration — `git diff --numstat`, `git status --porcelain`, `git rev-parse` |
| **JSON + JSONL** | Storage — no ORM, no migrations, no database, just files |
| **[Hatchling](https://hatch.pypa.io/)** | Build backend — modern Python packaging via `pyproject.toml` |

---

## Architecture

The CLI stays thin. Each module has one job. Each phase adds one folder.

```
agenttrace/
  cli.py              ← command definitions only, no business logic

  core/
    paths.py          ← every file path in one place, nothing hardcoded elsewhere
    session.py        ← Session Pydantic model
    storage.py        ← JSON read/write, init, current session helpers
    events.py         ← Event Pydantic model, JSONL append and read

  git/
    tracker.py        ← branch, status, diff --numstat, snapshot

  risk/               ← Phase 4: load rules.yaml, score commands and file paths
  reports/            ← Phase 5: build and save report.md
  integrations/       ← Phase 6: manage Claude Code hook installation
  hooks/              ← Phase 7: read hook JSON from stdin, auto-record events
```

---

## How AgentTrace Compares

There are several Claude Code tools out there. AgentTrace has a different focus.

| Tool | Focus |
|------|-------|
| Token trackers (claude-usage, etc.) | How many tokens did it use? What did it cost? |
| Real-time visualizers (agent-flow) | Watch the agent think as it runs |
| Multi-agent monitors (hooks-observability) | Observe distributed agent systems |
| **AgentTrace** | **What did it change in my code — and is it safe to merge?** |

AgentTrace is for developers who want to **review AI-generated code changes**, not just observe agent behavior.

---

## Design Principles

**Local-first.** All data stays in your project. Nothing leaves your machine, ever.

**No database.** JSON and JSONL only. Read any file with `cat` or a text editor.

**No background process.** AgentTrace runs only when you call it. Never passive, never watching.

**Non-destructive.** AgentTrace never modifies your code. It only observes and records.

**One phase at a time.** Each phase builds on the last. No skipping. No rewrites.

---

## Development

```bash
pytest                       # run the full test suite
agenttrace --help            # verify the CLI
pip install -e ".[dev]"      # reinstall after any changes
```

Tests use Typer's `CliRunner` with isolated temporary filesystems — no test ever touches your real project or Git repo.

---

## Roadmap

| Phase | Status | Description |
|-------|:------:|-------------|
| 0 | ✅ | Project setup — Typer, Rich, Pydantic, pytest, pyproject.toml |
| 1 | ✅ | Session tracking — `init`, `start`, `status` |
| 2 | ✅ | Event logging — `event command/file/note`, `events` |
| 3 | ✅ | Git tracking — `diff`, `snapshot` |
| 4 | 🔨 | Risk engine — score commands and file paths |
| 5 | 📋 | Report generator — auto-generate `report.md` |
| 6 | 📋 | Claude Code hooks — `claude setup/status/uninstall` |
| 7 | 📋 | Automatic recording via Claude Code hook events |
| 8 | 📋 | Polished terminal UI — Rich tables, colored risk badges |
| 11 | 📋 | Guard mode — block dangerous commands before they run |

---

## Contributing

Active early development — feedback and contributions welcome.

Good places to start:

- write more tests for edge cases in events, storage, and git tracker
- help design the risk scoring rules for Phase 4 — what counts as high risk?
- suggest what a useful `report.md` should look like
- report bugs or unexpected behavior

Run `pytest` before opening a PR.

---

## Author

Built by **Brahim Boughezroun** — [GitHub](https://github.com/Aa083824577)

Building in public, one phase at a time.

---

## License

MIT
