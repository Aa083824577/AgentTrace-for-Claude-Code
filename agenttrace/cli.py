from typing import Optional
import typer 
from rich.console import Console

app = typer.Typer(
    name="agenttrace",
    help="Observability and safety layer for Claude Code sessions.",
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
    console.print("[yellow]Phase 1 command placeholder:[/yellow] init")


@app.command()
def start(task: Optional[str] = typer.Argument(None)) -> None:
    """
    Start a new AgentTrace session.
    """
    if task:
        console.print(f"[green]Starting AgentTrace session:[/green] {task}")
    else:
        console.print("[green]Starting AgentTrace session[/green]")


@app.command()
def status() -> None:
    """
    Show the current AgentTrace session status.
    """
    console.print("[yellow]Phase 1 command placeholder:[/yellow] status")


@app.command()
def report() -> None:
    """
    Generate an AgentTrace report.
    """
    console.print("[yellow]Phase 5 command placeholder:[/yellow] report")