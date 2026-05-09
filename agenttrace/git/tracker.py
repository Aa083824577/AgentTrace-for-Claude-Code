import subprocess
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class GitError(RuntimeError):
    pass


class GitSummary(BaseModel):
    branch: str
    changed_files: list[str] = Field(default_factory=list)
    files_changed_count: int = 0
    insertions: int = 0
    deletions: int = 0
    raw_status: str = ""
    raw_stat: str = ""


def run_git_command(args: list[str], cwd: Path | None = None) -> str:
    working_dir = cwd or Path.cwd()

    try:
        result = subprocess.run(
            ["git", *args],
            cwd=working_dir,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as error:
        raise GitError("Git is not installed or not available in PATH.") from error

    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "Git command failed."
        raise GitError(message)

    return result.stdout.strip()


def is_git_repo(cwd: Path | None = None) -> bool:
    try:
        result = run_git_command(["rev-parse", "--is-inside-work-tree"], cwd=cwd)
        return result == "true"
    except GitError:
        return False


def require_git_repo(cwd: Path | None = None) -> None:
    if not is_git_repo(cwd=cwd):
        raise GitError("This project is not a Git repository.")


def get_current_branch(cwd: Path | None = None) -> str:
    require_git_repo(cwd=cwd)

    try:
        branch = run_git_command(["rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd)
    except GitError:
        return "unknown"

    if branch == "HEAD":
        return "detached"

    return branch


def get_git_status(cwd: Path | None = None) -> str:
    require_git_repo(cwd=cwd)
    return run_git_command(["status", "--porcelain"], cwd=cwd)


def get_git_diff_stat(cwd: Path | None = None) -> str:
    require_git_repo(cwd=cwd)
    return run_git_command(["diff", "--stat"], cwd=cwd)


def get_git_numstat(cwd: Path | None = None) -> str:
    require_git_repo(cwd=cwd)
    return run_git_command(["diff", "--numstat"], cwd=cwd)


def parse_changed_files(status_output: str) -> list[str]:
    changed_files: list[str] = []

    for line in status_output.splitlines():
        if not line.strip():
            continue

        # Git porcelain format usually looks like:
        # " M README.md"
        # "?? new_file.py"
        # "R  old.py -> new.py"
        path = line[3:].strip()

        if " -> " in path:
            path = path.split(" -> ")[-1].strip()

        changed_files.append(path)

    return changed_files


def parse_numstat(numstat_output: str) -> tuple[int, int]:
    insertions = 0
    deletions = 0

    for line in numstat_output.splitlines():
        parts = line.split("\t")

        if len(parts) < 3:
            continue

        added, removed, _path = parts[0], parts[1], parts[2]

        if added.isdigit():
            insertions += int(added)

        if removed.isdigit():
            deletions += int(removed)

    return insertions, deletions


def get_git_summary(cwd: Path | None = None) -> GitSummary:
    require_git_repo(cwd=cwd)

    branch = get_current_branch(cwd=cwd)
    status = get_git_status(cwd=cwd)
    raw_stat = get_git_diff_stat(cwd=cwd)
    numstat = get_git_numstat(cwd=cwd)

    changed_files = parse_changed_files(status)
    insertions, deletions = parse_numstat(numstat)

    return GitSummary(
        branch=branch,
        changed_files=changed_files,
        files_changed_count=len(changed_files),
        insertions=insertions,
        deletions=deletions,
        raw_status=status,
        raw_stat=raw_stat,
    )


def git_summary_to_dict(summary: GitSummary) -> dict[str, Any]:
    return summary.model_dump()