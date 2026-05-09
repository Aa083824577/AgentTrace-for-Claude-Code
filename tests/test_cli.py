from pathlib import Path

from typer.testing import CliRunner

from agenttrace.cli import app

runner = CliRunner()


def test_version_command():
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert "AgentTrace" in result.output
    assert "0.1.0" in result.output


def test_help_command():
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Observability and safety layer" in result.output


def test_init_creates_agenttrace_folder():
    with runner.isolated_filesystem():
        result = runner.invoke(app, ["init"])

        assert result.exit_code == 0
        assert "AgentTrace initialized" in result.output
        assert Path(".agenttrace").exists()
        assert Path(".agenttrace/sessions").exists()


def test_start_requires_init():
    with runner.isolated_filesystem():
        result = runner.invoke(app, ["start", "fix bug"])

        assert result.exit_code == 1
        assert "AgentTrace is not initialized" in result.output


def test_start_creates_session_after_init():
    with runner.isolated_filesystem():
        init_result = runner.invoke(app, ["init"])
        start_result = runner.invoke(app, ["start", "fix bug"])

        assert init_result.exit_code == 0
        assert start_result.exit_code == 0
        assert "AgentTrace session started" in start_result.output
        assert "fix bug" in start_result.output
        assert Path(".agenttrace/current_session.json").exists()


def test_status_shows_current_session():
    with runner.isolated_filesystem():
        runner.invoke(app, ["init"])
        runner.invoke(app, ["start", "fix bug"])

        result = runner.invoke(app, ["status"])

        assert result.exit_code == 0
        assert "fix bug" in result.output
        assert "running" in result.output


def test_event_command_requires_init():
    with runner.isolated_filesystem():
        result = runner.invoke(app, ["event", "command", "npm test"])

        assert result.exit_code == 1
        assert "AgentTrace is not initialized" in result.output


def test_event_command_requires_active_session():
    with runner.isolated_filesystem():
        runner.invoke(app, ["init"])

        result = runner.invoke(app, ["event", "command", "npm test"])

        assert result.exit_code == 1
        assert "No active AgentTrace session found" in result.output


def test_event_command_is_saved():
    with runner.isolated_filesystem():
        runner.invoke(app, ["init"])
        runner.invoke(app, ["start", "test event logging"])

        result = runner.invoke(app, ["event", "command", "npm test"])

        assert result.exit_code == 0
        assert "Command event recorded" in result.output

        session_dirs = list(Path(".agenttrace/sessions").iterdir())
        assert len(session_dirs) == 1

        events_file = session_dirs[0] / "events.jsonl"
        content = events_file.read_text()

        assert "command" in content
        assert "npm test" in content


def test_event_file_is_saved():
    with runner.isolated_filesystem():
        runner.invoke(app, ["init"])
        runner.invoke(app, ["start", "test file event"])

        result = runner.invoke(app, ["event", "file", "src/auth/login.ts"])

        assert result.exit_code == 0
        assert "File event recorded" in result.output

        session_dirs = list(Path(".agenttrace/sessions").iterdir())
        events_file = session_dirs[0] / "events.jsonl"
        content = events_file.read_text()

        assert "file" in content
        assert "src/auth/login.ts" in content


def test_event_note_is_saved():
    with runner.isolated_filesystem():
        runner.invoke(app, ["init"])
        runner.invoke(app, ["start", "test note event"])

        result = runner.invoke(app, ["event", "note", "Claude started debugging"])

        assert result.exit_code == 0
        assert "Note event recorded" in result.output

        session_dirs = list(Path(".agenttrace/sessions").iterdir())
        events_file = session_dirs[0] / "events.jsonl"
        content = events_file.read_text()

        assert "note" in content
        assert "Claude started debugging" in content


def test_events_are_appended_not_overwritten():
    with runner.isolated_filesystem():
        runner.invoke(app, ["init"])
        runner.invoke(app, ["start", "test append events"])

        runner.invoke(app, ["event", "command", "npm test"])
        runner.invoke(app, ["event", "file", "src/main.py"])
        runner.invoke(app, ["event", "note", "Finished first check"])

        session_dirs = list(Path(".agenttrace/sessions").iterdir())
        events_file = session_dirs[0] / "events.jsonl"
        lines = events_file.read_text().strip().splitlines()

        assert len(lines) == 3
        assert "npm test" in lines[0]
        assert "src/main.py" in lines[1]
        assert "Finished first check" in lines[2]


def test_events_command_lists_events():
    with runner.isolated_filesystem():
        runner.invoke(app, ["init"])
        runner.invoke(app, ["start", "test list events"])
        runner.invoke(app, ["event", "command", "npm test"])

        result = runner.invoke(app, ["events"])

        assert result.exit_code == 0
        assert "AgentTrace Events" in result.output
        assert "npm test" in result.output