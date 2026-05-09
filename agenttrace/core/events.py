import json
from datetime import datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from agenttrace.core.paths import session_events_file
from agenttrace.core.storage import get_current_session


EventType = Literal["command", "file", "note", "hook", "risk"]
RiskLevel = Literal["unknown", "low", "medium", "high"]


class Event(BaseModel):
    id: str
    type: EventType
    time: str
    message: str
    payload: dict[str, Any] = Field(default_factory=dict)
    risk: RiskLevel = "unknown"


def create_event(
    event_type: EventType,
    message: str,
    payload: dict[str, Any] | None = None,
    risk: RiskLevel = "unknown",
) -> Event:
    now = datetime.now()

    return Event(
        id=f"evt_{now.strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}",
        type=event_type,
        time=now.isoformat(timespec="seconds"),
        message=message,
        payload=payload or {},
        risk=risk,
    )


def get_current_session_events_file():
    session = get_current_session()

    if not session:
        raise RuntimeError('No active AgentTrace session found. Run: agenttrace start "your task"')

    if session.status != "running":
        raise RuntimeError("The current AgentTrace session is not running.")

    return session_events_file(session.id)


def append_event(event: Event) -> None:
    path = get_current_session_events_file()
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("a", encoding="utf-8") as file:
        file.write(event.model_dump_json() + "\n")


def record_event(
    event_type: EventType,
    message: str,
    payload: dict[str, Any] | None = None,
    risk: RiskLevel = "unknown",
) -> Event:
    event = create_event(
        event_type=event_type,
        message=message,
        payload=payload,
        risk=risk,
    )

    append_event(event)

    return event


def read_events() -> list[Event]:
    path = get_current_session_events_file()

    if not path.exists():
        return []

    events: list[Event] = []

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            data = json.loads(line)
            events.append(Event(**data))

    return events