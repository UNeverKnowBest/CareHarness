"""Minimal CareLoop Harness command-line interface."""

from typing import Annotated

import typer

from careloop import __version__

app = typer.Typer(
    add_completion=False,
    help="CareLoop Harness.",
    invoke_without_command=True,
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)


@app.callback()
def root(
    version: Annotated[
        bool,
        typer.Option("--version", help="Show the package version and exit."),
    ] = False,
) -> None:
    """Expose help and package version only."""
    if version:
        typer.echo(__version__)
        raise typer.Exit


def main() -> None:
    """Run the command-line application."""
    app()
