# AgentTrace

> **See exactly what Claude Code did. Before you trust it.**

AgentTrace is an open-source CLI tool that records every command run, every file touched, and every Git change made during a Claude Code session — then gives you a clean, local report to review before merging anything.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Typer](https://img.shields.io/badge/CLI-Typer-009688?style=flat)](https://typer.tiangolo.com/)
[![Pydantic](https://img.shields.io/badge/models-Pydantic-E92063?style=flat)](https://docs.pydantic.dev/)
[![Rich](https://img.shields.io/badge/terminal-Rich-7B2FBE?style=flat)](https://rich.readthedocs.io/)
[![License: MIT](https://img.shields.io/badge/license-MIT-22c55e?style=flat)](LICENSE)

---

## The Problem

You give Claude Code a task. It runs for a few minutes. It touches files, runs commands, rewrites things. Then it's done.

Now you're asking:

- What commands did it actually run?
- Did it touch `.env`, secrets, or any auth logic?
- How large is this diff really?
- Did it modify my tests?
- Can I safely merge this?

Without a record, you're manually digging through `git diff` and shell history hoping you catch everything. That's not a great way to trust AI-generated code.

AgentTrace solves this by acting as a **black-box recorder** for your Claude Code sessions.

---

## What It Does

AgentTrace sits alongside Claude Code and records everything into a clean local log inside your project. No cloud. No database. No background process.

**Currently working:**

- named coding sessions with start time and task description
- append-only JSONL event log — commands, files, and free notes
- Git tracking — branch, changed files, insertions, deletions
- Git snapshots saved directly into the session folder
- readable terminal output with Rich-powered tables

**Coming next:**

- risk scoring for commands and file paths (Phase 4)
- auto-generated Markdown session reports (Phase 5)
- Claude Code hook integration — records everything automatically, no manual logging needed (Phases 6–7)
- guard mode — blocks dangerous commands before they run (Phase 11)

---

## Built With

AgentTrace is built entirely in Python using tools chosen for simplicity, readability, and zero unnecessary dependencies.

| Tool | Role |
|------|------|
| [Python 3.11+](https://www.python.org/) | Core language |
| [Typer](https://typer.tiangolo.com/) | CLI framework — clean command definitions with type hints |
| [Rich](https://rich.readthedocs.io/) | Terminal output — tables, panels, colored status |
| [Pydantic v2](https://docs.pydantic.dev/) | Data models — Session, Event, GitSummary |
| [PyYAML](https://pyyaml.org/) | Risk rules config — `.agenttrace/rules.yaml` |
| [pytest](https://pytest.org/) | Testing — isolated filesystems, CLI runner |
| Git (subprocess) | Reading branch, diff, status, numstat |
| JSON + JSONL | Storage — no database, plain readable files |

No database. No web framework. No cloud SDK. Every dependency earns its place.

---

## Install

```bash
git clone https://github.com/YOUR_USERNAME/agenttrace.git
cd agenttrace

# macOS / Linux
python3 -m venv .venv && source .venv/bin/activate

# Windows PowerShell
python -m venv .venv && .venv\Scripts\Activate.ps1

pip install -e ".[dev]"
agenttrace --help
```

---

## Quickstart

```bash
# Initialize AgentTrace inside your project
agenttrace init

# Start a named session
agenttrace start "fix authentication bug"

# Log what Claude Code did
agenttrace event command "npm test"
agenttrace event command "npm run lint"
agenttrace event file "src/auth/login.ts"
agenttrace event file "src/auth/session.ts"
agenttrace event note "Claude rewrote the token refresh logic"

# Save git state
agenttrace snapshot

# Review the session
agenttrace events
agenttrace diff
agenttrace status
```

Once Claude Code hook integration ships (Phase 7), the logging steps above become fully automatic:

```bash
agenttrace init
agenttrace claude setup
agenttrace start "fix auth bug"
claude                       ← Claude Code runs, AgentTrace records everything
agenttrace report            ← Markdown report of the full session
```

---

## Example Output

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

  Git Changes
    src/auth/login.ts
    src/auth/session.ts
    tests/auth.test.ts

  Summary
    Files changed:  3
    Insertions:     120
    Deletions:      14
```

---

## How Data Is Stored

Everything lives inside `.agenttrace/` in your project. Readable without any special tools.

```
.agenttrace/
  current_session.json        ← pointer to the active session
  sessions/
    2026-05-08-155726/
      session.json            ← session metadata
      events.jsonl            ← append-only event log (one JSON per line)
      snapshot.json           ← git state captured mid-session
```

Each event is a single line of JSON:

```jsonl
{"id":"evt_20260508_160122_a1b2","type":"command","time":"2026-05-08T16:01:22","message":"npm test","payload":{"command":"npm test"},"risk":"unknown"}
{"id":"evt_20260508_160210_c3d4","type":"file","time":"2026-05-08T16:02:10","message":"src/auth/login.ts","payload":{"path":"src/auth/login.ts"},"risk":"unknown"}
{"id":"evt_20260508_160305_e5f6","type":"note","time":"2026-05-08T16:03:15","message":"Claude rewrote the token refresh logic","payload":{},"risk":"unknown"}
```

JSONL was chosen because it is append-only, inspectable with `cat`, and requires no parser to understand.

---

## Architecture

The codebase is structured so the CLI stays thin and each module has one clear job.

```
agenttrace/
  cli.py              ← commands only, no business logic

  core/
    paths.py          ← every file path defined in one place
    session.py        ← Session Pydantic model
    storage.py        ← JSON read/write, init, current session helpers
    events.py         ← Event Pydantic model, JSONL append + read

  git/
    tracker.py        ← git branch, status, diff --numstat, snapshot

  risk/               ← Phase 4: rules.yaml + command/file scorer
  reports/            ← Phase 5: Markdown report builder
  integrations/       ← Phase 6: .claude/settings.local.json setup
  hooks/              ← Phase 7: stdin hook handler for Claude Code
```

Each phase adds one module. Nothing gets rewritten.

---

## Roadmap

| Phase | Status | What It Adds |
|-------|--------|--------------|
| 0 | ✅ Done | Python project setup, `--help`, `version` |
| 1 | ✅ Done | `init`, `start`, `status` — session tracking |
| 2 | ✅ Done | `event command/file/note`, `events` — event logging |
| 3 | ✅ Done | `diff`, `snapshot` — Git tracking |
| 4 | 🔨 Next | `risk` — score commands and file paths |
| 5 | Planned | `report` — auto-generate `report.md` |
| 6 | Planned | `claude setup/status/uninstall` — hook installation |
| 7 | Planned | `hook pre-tool/post-tool/stop` — automatic recording |
| 8 | Planned | Rich tables, colored risk badges, polished output |
| 11 | Planned | Guard mode — block dangerous actions in real time |

---

## Design Principles

**Local-first.** Every file stays inside your project. Nothing is sent anywhere.

**No database.** JSON and JSONL files only. Open them with any text editor or `cat`.

**No background process.** AgentTrace runs only when you call it. It never watches passively.

**Non-destructive.** AgentTrace never modifies your code. It only observes and records.

**One phase at a time.** Each phase builds cleanly on the last. No skipping, no rewrites.

---

## Development

```bash
pytest                    # run the test suite
agenttrace --help         # verify the CLI works
pip install -e ".[dev]"   # reinstall after changes
```

Tests use `CliRunner` from Typer for CLI testing and isolated temporary filesystems so nothing touches your real project.

---

## Contributing

The project is in active early development. Good places to start:

- write more tests (events, storage, git tracker)
- improve Git diff parsing edge cases
- help design the risk scoring rules for Phase 4
- suggest what a useful `report.md` should look like

Run `pytest` before opening a PR.

---

## License

MIT
