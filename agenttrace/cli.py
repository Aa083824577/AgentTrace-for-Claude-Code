from typing import Optional
from agenttrace.risk.scorer import score_session
import typer
from rich.console import Console
from rich.table import Table
from agenttrace.reports.markdown import generate_report_for_current_session

from agenttrace.core.events import read_events, record_event
from agenttrace.core.paths import (
    agenttrace_dir,
    project_root,
    session_snapshot_file,
)
from agenttrace.core.session import create_session
from agenttrace.core.storage import (
    get_current_session,
    init_project,
    is_initialized,
    require_initialized,
    save_session,
    write_json,
)
from agenttrace.git.tracker import GitError, get_git_summary

app = typer.Typer(
    name="agenttrace",
    help="Observability and safety layer for Claude Code sessions.",
)

event_app = typer.Typer(
    help="Record events in the current AgentTrace session.",
)

console = Console()


@app.callback()
def main() -> None:
    """
    AgentTrace records commands, file changes, diffs, and risky actions
    during AI coding sessions.
    """


@app.command()
def version() -> None:
    """
    Show the AgentTrace version.
    """
    console.print("[bold green]AgentTrace[/bold green] version 0.1.0")


@app.command()
def init() -> None:
    """
    Initialize AgentTrace in the current project.
    """
    if is_initialized():
        console.print("[yellow]AgentTrace is already initialized.[/yellow]")
        console.print(f"Path: [bold]{agenttrace_dir()}[/bold]")
        return

    init_project()

    console.print("[bold green]AgentTrace initialized.[/bold green]")
    console.print(f"Created: [bold]{agenttrace_dir()}[/bold]")


@app.command()
def start(task: Optional[str] = typer.Argument(None)) -> None:
    """
    Start a new AgentTrace session.
    """
    try:
        require_initialized()
    except RuntimeError as error:
        console.print(f"[bold red]Error:[/bold red] {error}")
        raise typer.Exit(code=1)

    existing_session = get_current_session()

    if existing_session and existing_session.status == "running":
        console.print("[bold red]A session is already running.[/bold red]")
        console.print(f"Current session: [bold]{existing_session.task or existing_session.id}[/bold]")
        console.print("Finish it later with: agenttrace report")
        raise typer.Exit(code=1)

    session = create_session(task=task, project_path=project_root())
    save_session(session)

    console.print("[bold green]AgentTrace session started.[/bold green]")
    console.print(f"Session ID: [bold]{session.id}[/bold]")

    if task:
        console.print(f"Task: {task}")


@app.command()
def status() -> None:
    """
    Show the current AgentTrace session status.
    """
    try:
        require_initialized()
    except RuntimeError as error:
        console.print(f"[bold red]Error:[/bold red] {error}")
        raise typer.Exit(code=1)

    session = get_current_session()

    if not session:
        console.print("[yellow]No active AgentTrace session found.[/yellow]")
        return

    table = Table(title="AgentTrace Status")

    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("Session ID", session.id)
    table.add_row("Task", session.task or "No task provided")
    table.add_row("Project", session.project_path)
    table.add_row("Started At", session.started_at)
    table.add_row("Status", session.status)

    console.print(table)


@event_app.command("command")
def event_command(command: str = typer.Argument(...)) -> None:
    """
    Record a command event.
    """
    try:
        require_initialized()
        event = record_event(
            event_type="command",
            message=command,
            payload={"command": command},
        )
    except RuntimeError as error:
        console.print(f"[bold red]Error:[/bold red] {error}")
        raise typer.Exit(code=1)

    console.print("[bold green]Command event recorded.[/bold green]")
    console.print(f"Event ID: [bold]{event.id}[/bold]")
    console.print(f"Command: {command}")


@event_app.command("file")
def event_file(path: str = typer.Argument(...)) -> None:
    """
    Record a file event.
    """
    try:
        require_initialized()
        event = record_event(
            event_type="file",
            message=path,
            payload={"path": path},
        )
    except RuntimeError as error:
        console.print(f"[bold red]Error:[/bold red] {error}")
        raise typer.Exit(code=1)

    console.print("[bold green]File event recorded.[/bold green]")
    console.print(f"Event ID: [bold]{event.id}[/bold]")
    console.print(f"File: {path}")


@event_app.command("note")
def event_note(message: str = typer.Argument(...)) -> None:
    """
    Record a note event.
    """
    try:
        require_initialized()
        event = record_event(
            event_type="note",
            message=message,
            payload={},
        )
    except RuntimeError as error:
        console.print(f"[bold red]Error:[/bold red] {error}")
        raise typer.Exit(code=1)

    console.print("[bold green]Note event recorded.[/bold green]")
    console.print(f"Event ID: [bold]{event.id}[/bold]")
    console.print(f"Note: {message}")


@app.command("events")
def list_events() -> None:
    """
    List events from the current AgentTrace session.
    """
    try:
        require_initialized()
        events = read_events()
    except RuntimeError as error:
        console.print(f"[bold red]Error:[/bold red] {error}")
        raise typer.Exit(code=1)

    if not events:
        console.print("[yellow]No events recorded yet.[/yellow]")
        return

    table = Table(title="AgentTrace Events")

    table.add_column("Time", style="dim")
    table.add_column("Type", style="bold")
    table.add_column("Risk")
    table.add_column("Message")

    for event in events:
        table.add_row(
            event.time,
            event.type,
            event.risk,
            event.message,
        )

    console.print(table)


@app.command("diff")
def diff() -> None:
    """
    Show the current Git diff summary.
    """
    try:
        require_initialized()
        summary = get_git_summary()
    except RuntimeError as error:
        console.print(f"[bold red]Error:[/bold red] {error}")
        raise typer.Exit(code=1)
    except GitError as error:
        console.print(f"[bold red]Git error:[/bold red] {error}")
        raise typer.Exit(code=1)

    console.print(f"[bold]Branch:[/bold] {summary.branch}")

    if not summary.changed_files:
        console.print("[green]No Git changes detected.[/green]")
        return

    table = Table(title="Git Changes")
    table.add_column("File", style="bold")

    for file_path in summary.changed_files:
        table.add_row(file_path)

    console.print(table)

    console.print("[bold]Summary[/bold]")
    console.print(f"Files changed: [bold]{summary.files_changed_count}[/bold]")
    console.print(f"Insertions: [green]{summary.insertions}[/green]")
    console.print(f"Deletions: [red]{summary.deletions}[/red]")

    if summary.raw_stat:
        console.print()
        console.print("[bold]Raw git diff --stat[/bold]")
        console.print(summary.raw_stat)


@app.command("snapshot")
def snapshot() -> None:
    """
    Save the current Git state into the active AgentTrace session.
    """
    try:
        require_initialized()

        session = get_current_session()

        if not session:
            console.print(
                '[bold red]Error:[/bold red] No active AgentTrace session found. '
                'Run: agenttrace start "your task"'
            )
            raise typer.Exit(code=1)

        if session.status != "running":
            console.print("[bold red]Error:[/bold red] The current AgentTrace session is not running.")
            raise typer.Exit(code=1)

        summary = get_git_summary()
        snapshot_path = session_snapshot_file(session.id)
        write_json(snapshot_path, summary.model_dump())

    except RuntimeError as error:
        console.print(f"[bold red]Error:[/bold red] {error}")
        raise typer.Exit(code=1)
    except GitError as error:
        console.print(f"[bold red]Git error:[/bold red] {error}")
        raise typer.Exit(code=1)

    console.print("[bold green]Git snapshot saved.[/bold green]")
    console.print(f"Path: [bold]{snapshot_path}[/bold]")
    console.print(f"Branch: {summary.branch}")
    console.print(f"Files changed: {summary.files_changed_count}")


@app.command("risk")
def risk() -> None:
    """
    Score the current AgentTrace session risk.
    """
    try:
        require_initialized()
        events = read_events()

        try:
            git_summary = get_git_summary()
        except GitError:
            git_summary = None

        result = score_session(events=events, git_summary=git_summary)

    except RuntimeError as error:
        console.print(f"[bold red]Error:[/bold red] {error}")
        raise typer.Exit(code=1)

    risk_style = {
        "unknown": "dim",
        "low": "green",
        "medium": "yellow",
        "high": "red",
    }.get(result.level, "white")

    console.print(f"[bold]Session risk:[/bold] [{risk_style}]{result.level.upper()}[/{risk_style}]")

    if result.reasons:
        console.print()
        console.print("[bold]Reasons[/bold]")

        for reason in result.reasons:
            console.print(f"- {reason}")

    if result.matched_rules:
        console.print()
        console.print("[bold]Matched rules[/bold]")

        for rule in result.matched_rules:
            console.print(f"- {rule}")


@app.command()
def report() -> None:
    """
    Generate an AgentTrace Markdown report.
    """
    try:
        require_initialized()
        report_path = generate_report_for_current_session()
    except RuntimeError as error:
        console.print(f"[bold red]Error:[/bold red] {error}")
        raise typer.Exit(code=1)

    console.print("[bold green]AgentTrace report created.[/bold green]")
    console.print(f"Path: [bold]{report_path}[/bold]")
    

app.add_typer(event_app, name="event")