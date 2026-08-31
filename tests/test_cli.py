from typer.testing import CliRunner

from careloop import __version__
from careloop.cli import app

runner = CliRunner()


def test_cli_help_exposes_version_and_exact_business_commands() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "--version" in result.stdout
    assert "Commands" in result.stdout
    for command in ("evaluate", "replay", "benchmark"):
        assert command in result.stdout


def test_cli_version_matches_package_version() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.stdout.strip() == __version__
