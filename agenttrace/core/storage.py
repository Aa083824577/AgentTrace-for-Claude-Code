import json
from pathlib import Path
from typing import Any

from agenttrace.core.paths import (
    agenttrace_dir,
    current_session_file,
    session_events_file,
    session_file,
    sessions_dir,
)
from agenttrace.core.session import Session
from agenttrace.risk.rules import ensure_rules_file


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def is_initialized() -> bool:
    return agenttrace_dir().exists()


def init_project() -> None:
    agenttrace_dir().mkdir(exist_ok=True)
    sessions_dir().mkdir(exist_ok=True)
    ensure_rules_file()


def require_initialized() -> None:
    if not is_initialized():
        raise RuntimeError("AgentTrace is not initialized. Run: agenttrace init")


def save_session(session: Session) -> None:
    session_path = session_file(session.id)
    events_path = session_events_file(session.id)

    write_json(session_path, session.model_dump())
    write_json(current_session_file(), session.model_dump())

    if not events_path.exists():
        events_path.parent.mkdir(parents=True, exist_ok=True)
        events_path.touch()


def get_current_session() -> Session | None:
    path = current_session_file()

    if not path.exists():
        return None

    data = read_json(path)
    return Session(**data)