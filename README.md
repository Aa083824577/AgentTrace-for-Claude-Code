# AgentTrace

**Open-source observability and safety layer for Claude Code sessions.**

AgentTrace records commands, file events, Git changes, and session activity during AI-assisted coding workflows so developers can understand what happened before trusting or merging AI-generated code.

> AgentTrace is currently in early development. The CLI, session tracking, event logging, and Git tracking are working. Claude Code hook integration is planned.

---

## Why AgentTrace?

AI coding agents are powerful, but they can be difficult to trust.

When an AI coding agent works inside a project, it may:

- run terminal commands
- edit files
- modify tests
- touch configuration files
- change authentication or payment logic
- create large Git diffs
- run risky shell commands

After the session, developers often need to answer:

- What did the agent run?
- What files changed?
- How big was the diff?
- Did it touch sensitive files?
- Did it modify tests?
- Is this safe to review or merge?

AgentTrace is designed to answer those questions.

---

## What AgentTrace Does

AgentTrace acts like a **black-box recorder** for AI coding sessions.

It can currently:

- initialize local project tracing
- start an AgentTrace session
- store session metadata
- record command events
- record file events
- record note events
- list recorded events
- inspect Git changes
- show changed files
- count insertions and deletions
- save Git snapshots into the active session

Planned features:

- risk scoring
- Markdown reports
- Claude Code hook integration
- automatic command/file recording from Claude Code
- guard mode for blocking dangerous actions
- optional local dashboard

---

## Project Status

Current completed phases:

| Phase | Status | Description |
|---|---:|---|
| Phase 0 | Done | Python CLI project setup |
| Phase 1 | Done | Session tracking |
| Phase 2 | Done | Event logging |
| Phase 3 | Done | Git tracking |
| Phase 4 | Planned | Risk engine |
| Phase 5 | Planned | Markdown report generator |
| Phase 6 | Planned | Claude Code setup |
| Phase 7 | Planned | Claude Code hook recording |

---

## Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/agenttrace.git
cd agenttrace
```

Create and activate a virtual environment.

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Install AgentTrace in editable mode:

```bash
pip install -e ".[dev]"
```

Verify the CLI works:

```bash
agenttrace --help
```

---

## Quickstart

Initialize AgentTrace in a project:

```bash
agenttrace init
```

Start a tracing session:

```bash
agenttrace start "fix login bug"
```

Record a command event:

```bash
agenttrace event command "npm test"
```

Record a file event:

```bash
agenttrace event file "src/auth/login.ts"
```

Record a note:

```bash
agenttrace event note "Claude started debugging the login issue"
```

List recorded events:

```bash
agenttrace events
```

Inspect Git changes:

```bash
agenttrace diff
```

Save a Git snapshot:

```bash
agenttrace snapshot
```

Check session status:

```bash
agenttrace status
```

---

## Example CLI Output

### Session status

```text
AgentTrace Status

Session ID   2026-05-08-155726
Task         fix login bug
Project      C:\Users\hp\Desktop\agenttrace
Started At   2026-05-08T15:57:26
Status       running
```

### Events

```text
AgentTrace Events

Time                  Type      Risk       Message
2026-05-08T16:01:22   command   unknown    npm test
2026-05-08T16:02:10   file      unknown    src/auth/login.ts
2026-05-08T16:03:15   note      unknown    Claude started debugging
```

### Git diff summary

```text
Branch: main

Git Changes

README.md
agenttrace/cli.py
agenttrace/core/events.py

Summary

Files changed: 3
Insertions: 120
Deletions: 14
```

---

## How It Works

AgentTrace stores local tracing data inside the current project.

```text
.agenttrace/
  current_session.json
  sessions/
    <session-id>/
      session.json
      events.jsonl
      snapshot.json
```

### Session file

Each session represents one AI coding task.

```json
{
  "id": "2026-05-08-155726",
  "task": "fix login bug",
  "project_path": "C:\\Users\\hp\\Desktop\\agenttrace",
  "started_at": "2026-05-08T15:57:26",
  "ended_at": null,
  "status": "running"
}
```

### Event log

Events are stored as JSONL.

```jsonl
{"id":"evt_20260508_160122_abcd1234","type":"command","time":"2026-05-08T16:01:22","message":"npm test","payload":{"command":"npm test"},"risk":"unknown"}
{"id":"evt_20260508_160210_efgh5678","type":"file","time":"2026-05-08T16:02:10","message":"src/auth/login.ts","payload":{"path":"src/auth/login.ts"},"risk":"unknown"}
```

JSONL is used because it is simple, append-only, and easy to inspect.

---

## Current Commands

```bash
agenttrace --help
agenttrace version
agenttrace init
agenttrace start "task name"
agenttrace status
agenttrace event command "npm test"
agenttrace event file "src/auth/login.ts"
agenttrace event note "some note"
agenttrace events
agenttrace diff
agenttrace snapshot
agenttrace report
```

`agenttrace report` is currently a placeholder and will be implemented in a later phase.

---

## Architecture

```text
agenttrace/
  cli.py

  core/
    paths.py
    session.py
    storage.py
    events.py

  git/
    tracker.py

  risk/
    # planned

  reports/
    # planned

  integrations/
    # planned Claude Code integration

  hooks/
    # planned Claude Code hook handlers
```

### Main components

| Component | Purpose |
|---|---|
| `cli.py` | User-facing command line interface |
| `core/paths.py` | Centralized project path helpers |
| `core/session.py` | Session model and session creation |
| `core/storage.py` | JSON storage helpers |
| `core/events.py` | Event model, event writer, event reader |
| `git/tracker.py` | Git branch, status, diff, and snapshot logic |
| `risk/` | Planned risk scoring engine |
| `reports/` | Planned Markdown report generator |
| `integrations/` | Planned Claude Code setup integration |
| `hooks/` | Planned Claude Code hook event handlers |

---

## Git Tracking

AgentTrace does not secretly monitor your files.

It reads Git state only when you run:

```bash
agenttrace diff
```

or:

```bash
agenttrace snapshot
```

Internally, AgentTrace uses standard Git commands such as:

```bash
git rev-parse --abbrev-ref HEAD
git status --porcelain
git diff --stat
git diff --numstat
```

This allows AgentTrace to detect:

- current branch
- changed files
- number of changed files
- insertions
- deletions
- raw Git diff summary

---

## Planned Claude Code Integration

AgentTrace will later integrate with Claude Code using hooks.

Planned flow:

```text
Claude Code wants to run a tool
        ↓
Claude Code hook calls AgentTrace
        ↓
AgentTrace reads hook JSON from stdin
        ↓
AgentTrace records the command or file event
        ↓
AgentTrace generates a final report
```

Planned commands:

```bash
agenttrace claude setup
agenttrace claude status
agenttrace claude uninstall
agenttrace hook pre-tool
agenttrace hook post-tool
agenttrace hook stop
```

The goal is to make this final workflow possible:

```bash
agenttrace init
agenttrace claude setup
agenttrace start "fix auth bug"
claude
agenttrace report
```

---

## Roadmap

### Phase 4 — Risk Engine

Planned:

- create default risk rules
- add `.agenttrace/rules.yaml`
- score risky commands
- score risky files
- score changed Git files
- add `agenttrace risk`

Example future output:

```text
Session risk: Medium

Reasons:
- Modified authentication-related file: src/auth/login.ts
- Modified test file: tests/auth.test.ts
- No high-risk command detected
```

### Phase 5 — Markdown Reports

Planned:

- generate `report.md`
- include task summary
- include commands
- include files changed
- include Git diff summary
- include risk score
- include recommendation

### Phase 6 — Claude Code Setup

Planned:

- install Claude Code hooks
- safely update `.claude/settings.local.json`
- back up existing settings
- avoid overwriting user hooks

### Phase 7 — Hook Recording

Planned:

- read Claude Code hook JSON from stdin
- record Bash commands
- record Read/Edit/Write/MultiEdit file paths
- generate report on stop

### Later

Planned later features:

- guard mode
- dangerous command blocking
- local dashboard
- MCP support
- Codex/Cursor/Copilot support

---

## Development

Run tests:

```bash
pytest
```

Run the CLI locally:

```bash
agenttrace --help
```

Install after changes:

```bash
pip install -e ".[dev]"
```

---

## Design Principles

AgentTrace follows these principles:

- local-first
- simple file-based storage
- readable JSON/JSONL logs
- no database in the MVP
- no cloud dependency
- no hidden background process
- clear CLI output
- modular architecture
- one phase at a time

---

## Contributing

This project is in early development.

Good first areas to contribute:

- improve CLI output
- add tests
- improve Git parsing
- build the risk engine
- improve README examples
- add example reports

Before contributing, run:

```bash
pytest
```

---

## License

MIT License.
