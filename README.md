# AgentTrace

Open-source observability and safety layer for Claude Code.

AgentTrace records commands, file changes, diffs, and risky actions during AI coding sessions so developers can review what happened before trusting AI-generated code.

## Current Status

Phase 0: Project setup.

## Planned Features

- Claude Code hook integration
- Command logging
- Git diff tracking
- Risk scoring
- Markdown reports
- Guard mode for blocking dangerous actions

## Development Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
agenttrace --help