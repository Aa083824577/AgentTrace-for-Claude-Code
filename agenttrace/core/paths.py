from pathlib import Path

AGENTTRACE_DIR_NAME = ".agenttrace"


def project_root() -> Path:
    return Path.cwd()


def agenttrace_dir() -> Path:
    return project_root() / AGENTTRACE_DIR_NAME


def sessions_dir() -> Path:
    return agenttrace_dir() / "sessions"


def current_session_file() -> Path:
    return agenttrace_dir() / "current_session.json"


def session_dir(session_id: str) -> Path:
    return sessions_dir() / session_id


def session_file(session_id: str) -> Path:
    return session_dir(session_id) / "session.json"


def session_events_file(session_id: str) -> Path:
    return session_dir(session_id) / "events.jsonl"


def session_report_file(session_id: str) -> Path:
    return session_dir(session_id) / "report.md"


def session_snapshot_file(session_id: str) -> Path:
    return session_dir(session_id) / "snapshot.json"