from datetime import datetime
from pathlib import Path
from typing import Literal, Optional
from pydantic import BaseModel, Field


class Session(BaseModel):
    id: str
    task: Optional[str] = None
    project_path: str
    started_at: str
    ended_at: Optional[str] = None
    status: Literal["running", "completed"] = "running"


def create_session(task: Optional[str], project_path: Path) -> Session:
    now = datetime.now()
    session_id = now.strftime("%Y-%m-%d-%H%M%S")

    return Session(
        id=session_id,
        task=task,
        project_path=str(project_path),
        started_at=now.isoformat(timespec="seconds"),
        status="running",
    )