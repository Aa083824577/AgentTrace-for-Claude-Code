import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from agenttrace.core.events import record_event
from agenttrace.core.paths import session_raw_hook_file
from agenttrace.core.storage import get_current_session
from agenttrace.reports.markdown import generate_report_for_current_session


class HookPayloadError(RuntimeError):
    pass


def read_hook_payload_from_stdin() -> dict[str, Any]:
    raw_input = sys.stdin.read().strip()

    if not raw_input:
        return {}

    try:
        payload = json.loads(raw_input)
    except json.JSONDecodeError as error:
        raise HookPayloadError("Could not parse Claude hook JSON from stdin.") from error

    if not isinstance(payload, dict):
        raise HookPayloadError("Claude hook payload must be a JSON object.")

    return payload


def current_session_id() -> str:
    session = get_current_session()

    if not session:
        raise RuntimeError('No active AgentTrace session found. Run: agenttrace start "your task"')

    if session.status != "running":
        raise RuntimeError("The current AgentTrace session is not running.")

    return session.id


def save_raw_hook_payload(hook_name: str, payload: dict[str, Any]) -> Path:
    session_id = current_session_id()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique = uuid4().hex[:8]
    safe_hook_name = hook_name.replace(" ", "-").replace("_", "-")

    filename = f"{timestamp}_{safe_hook_name}_{unique}.json"
    path = session_raw_hook_file(session_id, filename)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    return path


def get_tool_name(payload: dict[str, Any]) -> str:
    tool_name = payload.get("tool_name")

    if isinstance(tool_name, str):
        return tool_name

    return "unknown"


def get_tool_input(payload: dict[str, Any]) -> dict[str, Any]:
    tool_input = payload.get("tool_input", {})

    if isinstance(tool_input, dict):
        return tool_input

    return {}


def extract_bash_command(payload: dict[str, Any]) -> str | None:
    tool_name = get_tool_name(payload)

    if tool_name != "Bash":
        return None

    tool_input = get_tool_input(payload)
    command = tool_input.get("command")

    if isinstance(command, str) and command.strip():
        return command.strip()

    return None


def extract_file_paths(payload: dict[str, Any]) -> list[str]:
    tool_name = get_tool_name(payload)
    tool_input = get_tool_input(payload)

    if tool_name not in {"Read", "Edit", "Write", "MultiEdit"}:
        return []

    paths: list[str] = []

    file_path = tool_input.get("file_path")

    if isinstance(file_path, str) and file_path.strip():
        paths.append(file_path.strip())

    # Future-safe support in case Claude sends multiple paths later.
    file_paths = tool_input.get("file_paths")

    if isinstance(file_paths, list):
        for item in file_paths:
            if isinstance(item, str) and item.strip():
                paths.append(item.strip())

    return list(dict.fromkeys(paths))


def record_hook_event(hook_name: str, payload: dict[str, Any], raw_path: Path) -> None:
    tool_name = get_tool_name(payload)

    record_event(
        event_type="hook",
        message=f"Claude hook received: {hook_name}",
        payload={
            "hook_name": hook_name,
            "tool_name": tool_name,
            "raw_payload_path": str(raw_path),
        },
    )


def handle_pre_tool() -> Path:
    payload = read_hook_payload_from_stdin()
    raw_path = save_raw_hook_payload("pre-tool", payload)

    # For Phase 7, pre-tool only records the hook itself.
    # Later Guard Mode will use this moment to block dangerous actions.
    record_hook_event("pre-tool", payload, raw_path)

    return raw_path


def handle_post_tool() -> Path:
    payload = read_hook_payload_from_stdin()
    raw_path = save_raw_hook_payload("post-tool", payload)

    record_hook_event("post-tool", payload, raw_path)

    command = extract_bash_command(payload)

    if command:
        record_event(
            event_type="command",
            message=command,
            payload={
                "command": command,
                "source": "claude_hook",
                "hook": "post-tool",
                "raw_payload_path": str(raw_path),
            },
        )

    file_paths = extract_file_paths(payload)

    for file_path in file_paths:
        record_event(
            event_type="file",
            message=file_path,
            payload={
                "path": file_path,
                "tool_name": get_tool_name(payload),
                "source": "claude_hook",
                "hook": "post-tool",
                "raw_payload_path": str(raw_path),
            },
        )

    return raw_path


def handle_stop() -> Path:
    payload = read_hook_payload_from_stdin()
    raw_path = save_raw_hook_payload("stop", payload)

    record_event(
        event_type="note",
        message="Claude Code session stopped.",
        payload={
            "source": "claude_hook",
            "hook": "stop",
            "raw_payload_path": str(raw_path),
        },
    )

    generate_report_for_current_session()

    return raw_path