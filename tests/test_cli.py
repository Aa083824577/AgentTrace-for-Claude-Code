from pathlib import Path

from typer.testing import CliRunner

from agenttrace.cli import app

runner = CliRunner()


def test_hook_pre_tool_requires_init():
    with runner.isolated_filesystem():
        result = runner.invoke(
            app,
            ["hook", "pre-tool"],
            input='{"tool_name":"Bash","tool_input":{"command":"npm test"}}',
        )

        assert result.exit_code == 1
        assert "AgentTrace is not initialized" in result.output


def test_hook_post_tool_records_bash_command():
    with runner.isolated_filesystem():
        runner.invoke(app, ["init"])
        runner.invoke(app, ["start", "test hook command"])

        result = runner.invoke(
            app,
            ["hook", "post-tool"],
            input='{"hook_event_name":"PostToolUse","tool_name":"Bash","tool_input":{"command":"npm test"}}',
        )

        assert result.exit_code == 0
        assert "post-tool hook recorded" in result.output

        session_dirs = list(Path(".agenttrace/sessions").iterdir())
        events_file = session_dirs[0] / "events.jsonl"

        content = events_file.read_text(encoding="utf-8")

        assert "npm test" in content
        assert "command" in content


def test_hook_post_tool_records_file_event():
    with runner.isolated_filesystem():
        runner.invoke(app, ["init"])
        runner.invoke(app, ["start", "test hook file"])

        result = runner.invoke(
            app,
            ["hook", "post-tool"],
            input='{"hook_event_name":"PostToolUse","tool_name":"Edit","tool_input":{"file_path":"src/auth/login.ts"}}',
        )

        assert result.exit_code == 0

        session_dirs = list(Path(".agenttrace/sessions").iterdir())
        events_file = session_dirs[0] / "events.jsonl"

        content = events_file.read_text(encoding="utf-8")

        assert "src/auth/login.ts" in content
        assert "file" in content


def test_hook_saves_raw_payload():
    with runner.isolated_filesystem():
        runner.invoke(app, ["init"])
        runner.invoke(app, ["start", "test raw hook"])

        runner.invoke(
            app,
            ["hook", "post-tool"],
            input='{"hook_event_name":"PostToolUse","tool_name":"Bash","tool_input":{"command":"npm test"}}',
        )

        session_dirs = list(Path(".agenttrace/sessions").iterdir())
        raw_hooks_dir = session_dirs[0] / "raw-hooks"

        assert raw_hooks_dir.exists()

        raw_files = list(raw_hooks_dir.glob("*.json"))

        assert len(raw_files) == 1
        assert "npm test" in raw_files[0].read_text(encoding="utf-8")


def test_hook_stop_generates_report():
    with runner.isolated_filesystem():
        runner.invoke(app, ["init"])
        runner.invoke(app, ["start", "test stop hook"])

        runner.invoke(
            app,
            ["hook", "post-tool"],
            input='{"hook_event_name":"PostToolUse","tool_name":"Bash","tool_input":{"command":"npm test"}}',
        )

        result = runner.invoke(
            app,
            ["hook", "stop"],
            input='{"hook_event_name":"Stop"}',
        )

        assert result.exit_code == 0
        assert "AgentTrace report generated" in result.output

        session_dirs = list(Path(".agenttrace/sessions").iterdir())
        report_file = session_dirs[0] / "report.md"

        assert report_file.exists()

        content = report_file.read_text(encoding="utf-8")

        assert "# AgentTrace Report" in content
        assert "npm test" in content


def test_hook_invalid_json_fails_cleanly():
    with runner.isolated_filesystem():
        runner.invoke(app, ["init"])
        runner.invoke(app, ["start", "test invalid json"])

        result = runner.invoke(
            app,
            ["hook", "post-tool"],
            input="{bad json",
        )

        assert result.exit_code == 1
        assert "Could not parse Claude hook JSON" in result.output