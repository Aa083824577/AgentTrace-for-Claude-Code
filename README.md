# AgentTrace

**Open-source observability and safety layer for Claude Code sessions.**

AgentTrace records what Claude Code does inside your project: commands, file activity, Git changes, risk signals, and final reports.

It helps developers answer one important question:

> What did the AI coding agent do, and should I trust the result?

---

## Why AgentTrace?

AI coding agents can read files, edit code, run commands, and change project state. That is powerful, but it creates a trust problem.

After an AI coding session, developers often need to know:

- What commands did the agent run?
- What files did it touch?
- Did it modify sensitive files?
- Did it change authentication, payments, config, or CI files?
- How large was the Git diff?
- Was anything risky?
- Is there a report I can review before merging?

AgentTrace acts like a **black-box recorder** for Claude Code sessions.

---

## Current Status

AgentTrace MVP is working.

| Phase | Status | Description |
|---|---:|---|
| Phase 0 | Done | Python CLI setup |
| Phase 1 | Done | Session tracking |
| Phase 2 | Done | Event logging |
| Phase 3 | Done | Git tracking |
| Phase 4 | Done | Risk engine |
| Phase 5 | Done | Markdown report generation |
| Phase 6 | Done | Claude Code setup integration |
| Phase 7 | Done | Claude Code hook recording |

---

## Features

AgentTrace currently supports:

- Local project initialization
- Session tracking
- Command event recording
- File event recording
- Note event recording
- Git diff inspection
- Git snapshot saving
- Risk scoring
- Markdown report generation
- Claude Code hook setup
- Claude Code hook status checks
- Claude Code hook uninstall
- Automatic Claude hook event handling
- Raw Claude hook payload logging for debugging

---

## Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/agenttrace.git
cd agenttrace
```

Create a virtual environment.

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

Install AgentTrace locally:

```bash
pip install -e ".[dev]"
```

Check that the CLI works:

```bash
agenttrace --help
```

---

## Quickstart

Initialize AgentTrace in your project:

```bash
agenttrace init
```

Start a session:

```bash
agenttrace start "fix login bug"
```

Record manual events:

```bash
agenttrace event command "npm test"
agenttrace event file "src/auth/login.ts"
agenttrace event note "Claude started debugging login"
```

List events:

```bash
agenttrace events
```

Inspect Git changes:

```bash
agenttrace diff
```

Score risk:

```bash
agenttrace risk
```

Generate a report:

```bash
agenttrace report
```

---

## Claude Code Integration

AgentTrace integrates with Claude Code using local hooks.

First initialize AgentTrace:

```bash
agenttrace init
```

Install Claude Code hooks:

```bash
agenttrace claude setup
```

Check hook status:

```bash
agenttrace claude status
```

Start a tracing session:

```bash
agenttrace start "real Claude Code test"
```

Then start Claude Code:

```bash
claude
```

Inside Claude Code, ask something like:

```text
Read README.md, run git status, then stop.
```

After Claude finishes, check what AgentTrace recorded:

```bash
agenttrace events
agenttrace risk
agenttrace report
```

Uninstall Claude hooks:

```bash
agenttrace claude uninstall
```

---

## How Claude Code Integration Works

AgentTrace writes hook configuration into:

```text
.claude/settings.local.json
```

Claude Code then calls AgentTrace during tool use:

```text
Claude Code uses a tool
        ↓
Claude Code fires a hook
        ↓
AgentTrace receives JSON through stdin
        ↓
AgentTrace records the event
        ↓
AgentTrace generates a report
```

AgentTrace handles:

```bash
agenttrace hook pre-tool
agenttrace hook post-tool
agenttrace hook stop
```

These commands are called automatically by Claude Code. You normally do not run them manually.

---

## Example Workflow

```bash
agenttrace init
agenttrace claude setup
agenttrace start "fix auth bug"
claude
```

Claude Code works on the task.

AgentTrace records:

- Bash commands
- Read/Edit/Write file activity
- Git changes
- Stop hook
- Raw Claude hook payloads

Then AgentTrace can generate a report:

```bash
agenttrace report
```

---

## Example Report

AgentTrace generates Markdown reports like this:

```md
# AgentTrace Report

## Task

fix auth bug

## Session

- Session ID: `2026-05-10-012934`
- Project: `C:\Users\hp\Desktop\agenttrace`
- Branch: `main`
- Started: `2026-05-10T01:29:34`
- Ended: `2026-05-10T01:31:58`
- Status: `completed`

## Summary

AgentTrace recorded **5 events**.

- Commands recorded: **1**
- File events recorded: **2**
- Git changed files: **3**
- Insertions: **82**
- Deletions: **21**
- Session risk: **MEDIUM**

## Commands Run

- `git status`

## File Events

- `README.md`
- `src/auth/login.ts`

## Risk

**MEDIUM**

## Recommendation

Review carefully before merge. Medium-risk files or actions were detected.
```

---

## Commands

### General

```bash
agenttrace --help
agenttrace version
```

### Project setup

```bash
agenttrace init
```

### Sessions

```bash
agenttrace start "task name"
agenttrace status
```

### Manual event recording

```bash
agenttrace event command "npm test"
agenttrace event file "README.md"
agenttrace event note "Manual note"
agenttrace events
```

### Git tracking

```bash
agenttrace diff
agenttrace snapshot
```

### Risk scoring

```bash
agenttrace risk
```

### Reports

```bash
agenttrace report
```

### Claude Code integration

```bash
agenttrace claude setup
agenttrace claude status
agenttrace claude uninstall
```

### Claude hook handlers

These are called by Claude Code automatically:

```bash
agenttrace hook pre-tool
agenttrace hook post-tool
agenttrace hook stop
```

---

## Data Storage

AgentTrace stores local data inside:

```text
.agenttrace/
```

Example structure:

```text
.agenttrace/
  current_session.json
  rules.yaml
  sessions/
    <session-id>/
      session.json
      events.jsonl
      snapshot.json
      report.md
      raw-hooks/
        20260510_013158_stop_d747e2d1.json
```

### `current_session.json`

Stores the current session:

```json
{
  "id": "2026-05-10-012934",
  "task": "real Claude Code user test",
  "project_path": "C:\\Users\\hp\\Desktop\\agenttrace",
  "started_at": "2026-05-10T01:29:34",
  "ended_at": "2026-05-10T01:31:58",
  "status": "completed"
}
```

### `events.jsonl`

Stores recorded events:

```jsonl
{"type":"command","message":"npm test","payload":{"command":"npm test"}}
{"type":"file","message":"README.md","payload":{"path":"README.md"}}
{"type":"note","message":"Claude Code session stopped."}
```

### `rules.yaml`

Stores risk rules:

```yaml
high_risk_commands:
  - rm -rf
  - sudo
  - chmod 777
  - git push --force

high_risk_files:
  - .env
  - .env.*
  - secrets/**
  - id_rsa
  - .github/workflows/**

medium_risk_paths:
  - auth/**
  - src/auth/**
  - payments/**
  - database/migrations/**
  - config/**

low_risk_paths:
  - README.md
  - docs/**
  - tests/**
```

---

## Risk Engine

AgentTrace scores risk using simple rule-based logic.

Examples:

| Activity | Risk |
|---|---:|
| `npm test` | Low |
| `README.md` | Low |
| `src/auth/login.ts` | Medium |
| `.env` | High |
| `rm -rf .` | High |
| `git push --force` | High |

Run:

```bash
agenttrace risk
```

Example output:

```text
Session risk: HIGH

Reasons
- Low-risk command recorded: npm test
- High-risk file touched: .env

Matched rules
- low_risk_commands: npm test
- high_risk_files: .env
```

---

## Git Tracking

AgentTrace does not run in the background.

It checks Git state when you run:

```bash
agenttrace diff
```

or:

```bash
agenttrace snapshot
```

Internally, it uses standard Git commands such as:

```bash
git status --porcelain
git diff --stat
git diff --numstat
git rev-parse --abbrev-ref HEAD
```

AgentTrace can detect:

- current branch
- changed files
- number of changed files
- insertions
- deletions
- raw Git diff summary

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
    rules.py
    scorer.py

  reports/
    markdown.py

  integrations/
    claude.py

  hooks/
    handler.py
```

### Components

| Component | Purpose |
|---|---|
| `cli.py` | User-facing CLI commands |
| `core/paths.py` | Path helpers |
| `core/session.py` | Session model |
| `core/storage.py` | JSON storage helpers |
| `core/events.py` | Event model and JSONL logging |
| `git/tracker.py` | Git status and diff inspection |
| `risk/rules.py` | Default and custom risk rules |
| `risk/scorer.py` | Command, file, Git, and session risk scoring |
| `reports/markdown.py` | Markdown report generation |
| `integrations/claude.py` | Claude Code hook setup/status/uninstall |
| `hooks/handler.py` | Claude Code hook payload handling |

---

## Development

Run tests:

```bash
pytest
```

Install locally after changes:

```bash
pip install -e ".[dev]"
```

Run CLI:

```bash
agenttrace --help
```

---

## Testing Claude Hook Handlers Manually

You can simulate Claude Code hook payloads without opening Claude Code.

Start a session:

```bash
agenttrace init
agenttrace start "hook test"
```

Simulate a file read:

```powershell
'{"hook_event_name":"PostToolUse","tool_name":"Read","tool_input":{"file_path":"README.md"}}' | agenttrace hook post-tool
```

Simulate a Bash command:

```powershell
'{"hook_event_name":"PostToolUse","tool_name":"Bash","tool_input":{"command":"git status"}}' | agenttrace hook post-tool
```

Check events:

```bash
agenttrace events
```

Simulate stop:

```powershell
'{"hook_event_name":"Stop"}' | agenttrace hook stop
```

Check report:

```bash
agenttrace report
```

---

## Troubleshooting

### `AgentTrace is not initialized`

Run:

```bash
agenttrace init
```

### `No active AgentTrace session found`

Start a session:

```bash
agenttrace start "task name"
```

### `The current AgentTrace session is not running`

The session is probably completed.

Check:

```bash
agenttrace status
```

or:

```bash
cat .agenttrace/current_session.json
```

Start a new session if needed.

### Claude hooks are not installed

Run:

```bash
agenttrace claude setup
agenttrace claude status
```

### Claude hook errors

Check raw hook payloads:

```powershell
Get-ChildItem .agenttrace\sessions\*\raw-hooks
```

Open a raw hook file:

```powershell
Get-Content .agenttrace\sessions\<session-id>\raw-hooks\<file-name>.json
```

---

## Roadmap

Next possible improvements:

- Better report formatting
- Better CLI summaries
- GitHub Actions CI
- Example reports
- Demo GIF or video
- Guard mode for blocking dangerous commands
- Configurable risk levels
- Local dashboard
- MCP support
- Codex/Cursor/Copilot integrations

---

## What AgentTrace Does Not Do Yet

AgentTrace currently does not:

- block dangerous commands
- upload data to a server
- provide a web dashboard
- support multiple coding agents
- replace code review
- install Claude Code itself

AgentTrace records and analyzes local AI coding activity.

---

## Design Principles

- Local-first
- Open-source
- File-based storage
- Human-readable logs
- Simple CLI
- No cloud dependency
- No database required for MVP
- Works with Claude Code hooks
- Easy to inspect and debug

---

## Contributing

Contributions are welcome.

Good first tasks:

- Improve CLI output
- Add tests
- Improve report formatting
- Improve risk rules
- Add example reports
- Add GitHub Actions CI
- Improve Claude hook payload parsing

Before submitting changes:

```bash
pytest
```

---

## License

MIT License.
