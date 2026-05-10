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


def read_raw_stdin() -> str:
    return sys.stdin.read()


def parse_hook_payload(raw_input: str) -> dict[str, Any]:
    raw_input = raw_input.strip()

    if not raw_input:
        return {}

    try:
        payload = json.loads(raw_input)
    except json.JSONDecodeError as error:
        raise HookPayloadError(f"Could not parse Claude hook JSON from stdin: {error}") from error

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


def save_raw_hook_debug(
    hook_name: str,
    raw_input: str,
    payload: dict[str, Any] | None = None,
    error: str | None = None,
) -> Path:
    session_id = current_session_id()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique = uuid4().hex[:8]
    safe_hook_name = hook_name.replace(" ", "-").replace("_", "-")

    filename = f"{timestamp}_{safe_hook_name}_{unique}.json"
    path = session_raw_hook_file(session_id, filename)

    debug_payload = {
        "hook_name": hook_name,
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "raw_input": raw_input,
        "payload": payload,
        "error": error,
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(debug_payload, indent=2), encoding="utf-8")

    return path


def get_nested_dict(payload: dict[str, Any], *keys: str) -> dict[str, Any]:
    current: Any = payload

    for key in keys:
        if not isinstance(current, dict):
            return {}

        current = current.get(key)

    if isinstance(current, dict):
        return current

    return {}


def get_tool_name(payload: dict[str, Any]) -> str:
    candidates = [
        payload.get("tool_name"),
        payload.get("tool"),
        get_nested_dict(payload, "tool").get("name"),
        get_nested_dict(payload, "tool_use").get("name"),
    ]

    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()

    return "unknown"


def get_tool_input(payload: dict[str, Any]) -> dict[str, Any]:
    candidates = [
        payload.get("tool_input"),
        payload.get("input"),
        payload.get("params"),
        get_nested_dict(payload, "tool").get("input"),
        get_nested_dict(payload, "tool_use").get("input"),
    ]

    for candidate in candidates:
        if isinstance(candidate, dict):
            return candidate

    return {}


def extract_bash_command(payload: dict[str, Any]) -> str | None:
    tool_name = get_tool_name(payload)

    if tool_name != "Bash":
        return None

    tool_input = get_tool_input(payload)

    for key in ["command", "cmd", "bash_command"]:
        value = tool_input.get(key)

        if isinstance(value, str) and value.strip():
            return value.strip()

    return None


def extract_file_paths(payload: dict[str, Any]) -> list[str]:
    tool_name = get_tool_name(payload)
    tool_input = get_tool_input(payload)

    if tool_name not in {"Read", "Edit", "Write", "MultiEdit"}:
        return []

    paths: list[str] = []

    for key in ["file_path", "path", "file", "target_file"]:
        value = tool_input.get(key)

        if isinstance(value, str) and value.strip():
            paths.append(value.strip())

    for key in ["file_paths", "paths"]:
        value = tool_input.get(key)

        if isinstance(value, list):
            for item in value:
                if isinstance(item, str) and item.strip():
                    paths.append(item.strip())

    edits = tool_input.get("edits")

    if isinstance(edits, list):
        for edit in edits:
            if isinstance(edit, dict):
                file_path = edit.get("file_path") or edit.get("path")

                if isinstance(file_path, str) and file_path.strip():
                    paths.append(file_path.strip())

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


def record_extracted_activity(hook_name: str, payload: dict[str, Any], raw_path: Path) -> None:
    command = extract_bash_command(payload)

    if command:
        record_event(
            event_type="command",
            message=command,
            payload={
                "command": command,
                "source": "claude_hook",
                "hook": hook_name,
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
                "hook": hook_name,
                "raw_payload_path": str(raw_path),
            },
        )


def handle_tool_hook(hook_name: str) -> Path:
    raw_input = read_raw_stdin()

    try:
        payload = parse_hook_payload(raw_input)
    except HookPayloadError as error:
        raw_path = save_raw_hook_debug(
            hook_name=hook_name,
            raw_input=raw_input,
            payload=None,
            error=str(error),
        )
        raise HookPayloadError(f"{error}. Raw payload saved to: {raw_path}") from error

    raw_path = save_raw_hook_debug(
        hook_name=hook_name,
        raw_input=raw_input,
        payload=payload,
        error=None,
    )

    record_hook_event(hook_name, payload, raw_path)
    record_extracted_activity(hook_name, payload, raw_path)

    return raw_path


def handle_pre_tool() -> Path:
    return handle_tool_hook("pre-tool")


def handle_post_tool() -> Path:
    return handle_tool_hook("post-tool")


def handle_stop() -> Path:
    raw_input = read_raw_stdin()

    try:
        payload = parse_hook_payload(raw_input)
    except HookPayloadError as error:
        raw_path = save_raw_hook_debug(
            hook_name="stop",
            raw_input=raw_input,
            payload=None,
            error=str(error),
        )
        raise HookPayloadError(f"{error}. Raw payload saved to: {raw_path}") from error

    raw_path = save_raw_hook_debug(
        hook_name="stop",
        raw_input=raw_input,
        payload=payload,
        error=None,
    )

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