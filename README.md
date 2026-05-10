# AgentTrace for Claude Code

**You let Claude Code run. Now what did it actually do?**

AgentTrace is an open-source CLI tool that sits alongside Claude Code and records everything that happens during a coding session — every command run, every file touched, every Git change made — stored locally as plain files inside your project, so you can review it all before trusting or merging anything.

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Typer](https://img.shields.io/badge/CLI-Typer-009688?style=flat-square)](https://typer.tiangolo.com/)
[![Pydantic v2](https://img.shields.io/badge/Models-Pydantic_v2-E92063?style=flat-square)](https://docs.pydantic.dev/)
[![Rich](https://img.shields.io/badge/Terminal-Rich-7B2FBE?style=flat-square)](https://rich.readthedocs.io/)
[![pytest](https://img.shields.io/badge/Tests-pytest-0A9EDC?style=flat-square)](https://pytest.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active_Development-orange?style=flat-square)]()

---

## The Problem

You give Claude Code a task. It runs for a few minutes — editing files, running commands, touching configuration, rewriting logic. Then it stops.

And you're left asking:

- What commands did it actually run?
- Did it touch `.env`, secrets, or any auth code?
- Did it modify my tests?
- How big is this diff really?
- Is this safe to merge?

Without a record, you're manually piecing together `git diff` and shell history every single time. That is not a good trust model for AI-generated code.

**AgentTrace fixes this** by keeping a clean, local, append-only log of everything that happened during the session — so you can answer all those questions before you merge anything.

---

## What's Working Right Now

Phases 0 through 3 are complete.

```bash
agenttrace init                                 # set up AgentTrace in any project
agenttrace start "fix authentication bug"       # begin a named session
agenttrace event command "npm test"             # record a command that ran
agenttrace event file "src/auth/login.ts"       # record a file that was touched
agenttrace event note "rewrote token refresh"   # attach a free-text note
agenttrace events                               # list everything that happened
agenttrace diff                                 # inspect git changes
agenttrace snapshot                             # save git state mid-session
agenttrace status                               # check the current session
agenttrace version                              # show version
```

**Coming next:**

| Command | Phase | What it does |
|---------|:-----:|--------------|
| `agenttrace risk` | 4 | Score commands and files as low / medium / high risk |
| `agenttrace report` | 5 | Auto-generate a full Markdown session report |
| `agenttrace claude setup` | 6 | Install Claude Code hooks — automatic recording, no manual logging |
| `agenttrace hook ...` | 7 | Handle hook events from Claude Code in real time |
| Guard mode | 11 | Block dangerous commands before they run |

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

## A Full Session, Step by Step

```bash
# Once per project
agenttrace init

# Before you open Claude Code
agenttrace start "fix authentication bug"

# After Claude Code finishes — record what it did
agenttrace event command "npm test"
agenttrace event command "npm run lint"
agenttrace event file "src/auth/login.ts"
agenttrace event file "src/auth/session.ts"
agenttrace event note "Claude rewrote the token refresh logic"

# Capture the git state at this point
agenttrace snapshot

# Review everything
agenttrace events
agenttrace diff
```

Once Phase 7 ships, the manual recording steps become fully automatic:

```bash
agenttrace init
agenttrace claude setup          # install Claude Code hooks once
agenttrace start "fix auth bug"
claude                           # Claude Code works — AgentTrace records automatically
agenttrace report                # full Markdown report of everything that happened
```

---

## What the Output Looks Like

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
  2026-05-08T16:03:15   note      unknown    Claude rewrote the token refresh logic
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

**`agenttrace risk` — coming in Phase 4**

```
Session Risk: MEDIUM

  Reasons
    · Modified authentication file: src/auth/login.ts
    · Modified authentication file: src/auth/session.ts
    · Test file modified: tests/auth.test.ts
    · No high-risk shell commands detected

  Recommendation
    Review carefully before merging.
```

---

## How Data Is Stored

Everything is local. No cloud. No server. No background process. Just files inside your project.

```
.agenttrace/
  current_session.json          ← points to the active session
  sessions/
    2026-05-08-155726/
      session.json              ← session metadata (task, status, timestamps)
      events.jsonl              ← append-only event log, one JSON object per line
      snapshot.json             ← git state captured at snapshot time
```

Events are plain JSONL — readable with `cat`, no tooling required:

```jsonl
{"id":"evt_20260508_160122_a1b2","type":"command","time":"2026-05-08T16:01:22","message":"npm test","payload":{"command":"npm test"},"risk":"unknown"}
{"id":"evt_20260508_160210_c3d4","type":"file","time":"2026-05-08T16:02:10","message":"src/auth/login.ts","payload":{"path":"src/auth/login.ts"},"risk":"unknown"}
{"id":"evt_20260508_160305_e5f6","type":"note","time":"2026-05-08T16:03:15","message":"Claude rewrote the token refresh logic","payload":{},"risk":"unknown"}
```

JSONL was chosen deliberately: append-only, human-readable, no parser needed, no database to manage.

---

## Built With

Every dependency earns its place. Nothing included for convenience.

| Tool | Role |
|------|------|
| **[Python 3.11+](https://www.python.org/)** | Core language — type hints, modern stdlib, match statements |
| **[Typer](https://typer.tiangolo.com/)** | CLI framework — commands defined from Python type annotations, built on Click |
| **[Rich](https://rich.readthedocs.io/)** | Terminal output — tables, panels, colored text without fighting ANSI codes |
| **[Pydantic v2](https://docs.pydantic.dev/)** | Data models — `Session`, `Event`, `GitSummary` with validation and JSON serialization |
| **[PyYAML](https://pyyaml.org/)** | Risk rules config — `.agenttrace/rules.yaml` for per-project customization (Phase 4) |
| **[pytest](https://pytest.org/)** | Tests — `CliRunner` for CLI testing, isolated temp filesystems per test |
| **subprocess + Git** | Git integration — `git diff --numstat`, `git status --porcelain`, `git rev-parse` |
| **JSON + JSONL** | Storage — no ORM, no migrations, no database engine, just files |
| **[Hatchling](https://hatch.pypa.io/)** | Build backend — modern Python packaging via `pyproject.toml` |

No database. No web framework. No cloud SDK.

---

## Architecture

The CLI stays thin. Each module has one job. Each phase adds one folder.

```
agenttrace/
  cli.py              ← command definitions only, no business logic

  core/
    paths.py          ← every file path in one place — nothing hardcoded elsewhere
    session.py        ← Session Pydantic model
    storage.py        ← JSON read/write, init, current session helpers
    events.py         ← Event Pydantic model, JSONL append and read

  git/
    tracker.py        ← branch, status, diff --numstat, snapshot

  risk/               ← Phase 4: load rules.yaml, score commands and file paths
  reports/            ← Phase 5: build and save report.md
  integrations/       ← Phase 6: install and manage Claude Code hooks
  hooks/              ← Phase 7: read hook JSON from stdin, record events automatically
```

---

## Roadmap

| Phase | Status | Description |
|-------|:------:|-------------|
| 0 | ✅ | Python project setup — Typer, Rich, Pydantic, pytest, pyproject.toml |
| 1 | ✅ | Session tracking — `init`, `start`, `status` |
| 2 | ✅ | Event logging — `event command / file / note`, `events` |
| 3 | ✅ | Git tracking — `diff`, `snapshot` |
| 4 | 🔨 | Risk engine — score every command and file path |
| 5 | 📋 | Report generator — auto-generate `report.md` |
| 6 | 📋 | Claude Code integration — `claude setup / status / uninstall` |
| 7 | 📋 | Hook handlers — fully automatic recording via Claude Code hooks |
| 8 | 📋 | Terminal UI polish — Rich tables, colored risk badges |
| 11 | 📋 | Guard mode — block dangerous actions before they run |

---

## Design Principles

**Local-first.** All data stays inside your project. Nothing ever leaves your machine.

**No database.** JSON and JSONL files only. Read anything with `cat` or a text editor — no tooling needed.

**No background process.** AgentTrace runs only when you call it. It never watches, polls, or runs silently.

**Non-destructive.** AgentTrace never modifies your code. It only observes and records.

**One phase at a time.** Each phase builds cleanly on the previous one. No skipping. No full rewrites.

---

## Development

```bash
pytest                       # run the full test suite
agenttrace --help            # verify the CLI
pip install -e ".[dev]"      # reinstall after changes
```

Tests use Typer's `CliRunner` and temporary isolated filesystems — no test ever touches your real project or real Git repo.

---

## Contributing

Active early development — contributions welcome.

Good places to start:

- write more tests for events, storage, and the Git tracker
- help design the risk scoring rules for Phase 4 — what counts as high risk?
- suggest what a useful `report.md` should actually look like
- improve Git diff parsing for edge cases

Run `pytest` before opening a PR.

---

## Author

Built by **Brahim Boughezroun** — [GitHub](https://github.com/Aa083824577)

---

## License

MIT
