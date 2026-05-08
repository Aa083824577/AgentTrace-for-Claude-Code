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