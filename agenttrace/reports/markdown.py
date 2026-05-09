from datetime import datetime
from pathlib import Path
from agenttrace.core.events import Event, read_events_for_session
from agenttrace.core.paths import session_report_file
from agenttrace.core.session import Session
from agenttrace.core.storage import get_current_session, save_session
from agenttrace.git.tracker import GitError, GitSummary, get_git_summary
from agenttrace.risk.scorer import RiskResult, score_session


def escape_markdown_table_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def recommendation_for_risk(level: str) -> str:
    if level == "high":
        return "Do not merge until manually reviewed. High-risk activity was detected."

    if level == "medium":
        return "Review carefully before merge. Medium-risk files or actions were detected."

    if level == "low":
        return "Looks safe for normal review. Low-risk activity was detected."

    return "Not enough information to make a strong recommendation."


def events_markdown(events: list[Event]) -> str:
    if not events:
        return "No events were recorded.\n"

    lines = [
        "| Time | Type | Risk | Message |",
        "|---|---|---|---|",
    ]

    for event in events:
        lines.append(
            "| "
            f"{escape_markdown_table_cell(event.time)} | "
            f"{escape_markdown_table_cell(event.type)} | "
            f"{escape_markdown_table_cell(event.risk)} | "
            f"{escape_markdown_table_cell(event.message)} |"
        )

    return "\n".join(lines) + "\n"


def commands_markdown(events: list[Event]) -> str:
    command_events = [event for event in events if event.type == "command"]

    if not command_events:
        return "No command events were recorded.\n"

    lines = []

    for event in command_events:
        command = event.payload.get("command", event.message)
        lines.append(f"- `{command}`")

    return "\n".join(lines) + "\n"


def file_events_markdown(events: list[Event]) -> str:
    file_events = [event for event in events if event.type == "file"]

    if not file_events:
        return "No file events were recorded.\n"

    lines = []

    for event in file_events:
        path = event.payload.get("path", event.message)
        lines.append(f"- `{path}`")

    return "\n".join(lines) + "\n"


def git_changes_markdown(git_summary: GitSummary | None) -> str:
    if git_summary is None:
        return "Git information was unavailable.\n"

    if not git_summary.changed_files:
        return "No Git changes detected.\n"

    lines = []

    for file_path in git_summary.changed_files:
        lines.append(f"- `{file_path}`")

    return "\n".join(lines) + "\n"


def risk_reasons_markdown(risk_result: RiskResult) -> str:
    if not risk_result.reasons:
        return "No risk reasons were recorded.\n"

    lines = []

    for reason in risk_result.reasons:
        lines.append(f"- {reason}")

    return "\n".join(lines) + "\n"


def matched_rules_markdown(risk_result: RiskResult) -> str:
    if not risk_result.matched_rules:
        return "No rules were matched.\n"

    lines = []

    for rule in risk_result.matched_rules:
        lines.append(f"- `{rule}`")

    return "\n".join(lines) + "\n"


def build_markdown_report(
    session: Session,
    events: list[Event],
    git_summary: GitSummary | None,
    risk_result: RiskResult,
) -> str:
    command_count = len([event for event in events if event.type == "command"])
    file_event_count = len([event for event in events if event.type == "file"])

    git_changed_count = git_summary.files_changed_count if git_summary else 0
    insertions = git_summary.insertions if git_summary else 0
    deletions = git_summary.deletions if git_summary else 0
    branch = git_summary.branch if git_summary else "unknown"

    recommendation = recommendation_for_risk(risk_result.level)

    return f"""# AgentTrace Report

## Task

{session.task or "No task provided"}

## Session

- Session ID: `{session.id}`
- Project: `{session.project_path}`
- Branch: `{branch}`
- Started: `{session.started_at}`
- Ended: `{session.ended_at or "Not ended"}`
- Status: `{session.status}`

## Summary

AgentTrace recorded **{len(events)} events**.

- Commands recorded: **{command_count}**
- File events recorded: **{file_event_count}**
- Git changed files: **{git_changed_count}**
- Insertions: **{insertions}**
- Deletions: **{deletions}**
- Session risk: **{risk_result.level.upper()}**

## Events

{events_markdown(events)}

## Commands Run

{commands_markdown(events)}

## File Events

{file_events_markdown(events)}

## Git Changes

{git_changes_markdown(git_summary)}

## Diff Summary

- Files changed: **{git_changed_count}**
- Insertions: **{insertions}**
- Deletions: **{deletions}**

## Risk

**{risk_result.level.upper()}**

## Risk Reasons

{risk_reasons_markdown(risk_result)}

## Matched Rules

{matched_rules_markdown(risk_result)}

## Recommendation

{recommendation}
"""


def generate_report_for_current_session(mark_completed: bool = True) -> Path:
    session = get_current_session()

    if not session:
        raise RuntimeError('No active AgentTrace session found. Run: agenttrace start "your task"')

    events = read_events_for_session(session.id)

    try:
        git_summary = get_git_summary()
    except GitError:
        git_summary = None

    risk_result = score_session(events=events, git_summary=git_summary)

    if mark_completed:
        session.status = "completed"
        session.ended_at = datetime.now().isoformat(timespec="seconds")

    markdown = build_markdown_report(
        session=session,
        events=events,
        git_summary=git_summary,
        risk_result=risk_result,
    )

    report_path = session_report_file(session.id)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(markdown, encoding="utf-8")

    if mark_completed:
        save_session(session)

    return report_path