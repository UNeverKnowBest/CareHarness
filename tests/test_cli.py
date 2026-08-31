import re

from typer.testing import CliRunner

from careloop import __version__
from careloop.cli import app

runner = CliRunner()
ANSI_ESCAPE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def test_cli_help_exposes_version_and_exact_business_commands() -> None:
    result = runner.invoke(app, ["--help"], color=True)
    help_text = ANSI_ESCAPE.sub("", result.stdout)

    assert result.exit_code == 0
    assert "--version" in help_text
    assert "Commands" in help_text
    for command in ("evaluate", "replay", "benchmark"):
        assert command in help_text


def test_cli_version_matches_package_version() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.stdout.strip() == __version__
