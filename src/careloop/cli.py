"""Offline CareLoop Harness command-line composition root."""

from pathlib import Path
from typing import Annotated, NoReturn

import typer

from careloop import __version__
from careloop.application import (
    BenchmarkReportPaths,
    EvaluateTrajectory,
    RunBenchmark,
    replay_artifact,
)
from careloop.presentation import write_static_audit

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
    """Evaluate and audit frozen synthetic trajectory artifacts."""
    if version:
        typer.echo(__version__)
        raise typer.Exit


DEFAULT_MANIFEST = Path("benchmarks/manifest.v1.json")
DEFAULT_PROCESS_POLICY = Path("policies/process.v1.json")
DEFAULT_CRISIS_POLICY = Path("policies/crisis.v1.json")
DEFAULT_RESOURCE_POLICY = Path("policies/resources.v1.json")
DEFAULT_EVALUATION_POLICY = Path("policies/evaluation.v1.json")


def _fail(exc: BaseException) -> NoReturn:
    typer.echo(f"Error: {exc}", err=True)
    raise typer.Exit(code=1)


def _evaluate_service(
    *,
    manifest: Path,
    process_policy: Path,
    crisis_policy: Path,
    resource_policy: Path,
    evaluation_policy: Path,
) -> EvaluateTrajectory:
    return EvaluateTrajectory.from_paths(
        benchmark_manifest_path=manifest,
        process_policy_path=process_policy,
        crisis_policy_path=crisis_policy,
        resource_policy_path=resource_policy,
        evaluation_policy_path=evaluation_policy,
    )


@app.command()
def evaluate(
    artifact: Annotated[Path, typer.Argument(help="Canonical frozen trajectory JSON.")],
    manifest: Annotated[
        Path,
        typer.Option("--manifest", help="Benchmark manifest providing frozen as_of."),
    ] = DEFAULT_MANIFEST,
    output: Annotated[
        Path | None,
        typer.Option("--output", help="Canonical raw evaluation JSON path."),
    ] = None,
    audit_html: Annotated[
        Path | None,
        typer.Option("--audit-html", help="Static offline evidence audit path."),
    ] = None,
    process_policy: Annotated[
        Path, typer.Option("--process-policy", help="Process policy registry.")
    ] = DEFAULT_PROCESS_POLICY,
    crisis_policy: Annotated[
        Path, typer.Option("--crisis-policy", help="Crisis policy registry.")
    ] = DEFAULT_CRISIS_POLICY,
    resource_policy: Annotated[
        Path, typer.Option("--resource-policy", help="Resource policy registry.")
    ] = DEFAULT_RESOURCE_POLICY,
    evaluation_policy: Annotated[
        Path,
        typer.Option("--evaluation-policy", help="Offline observation registry."),
    ] = DEFAULT_EVALUATION_POLICY,
) -> None:
    """Evaluate one frozen artifact and write an evidence ledger plus audit HTML."""
    raw_path = output or Path("artifacts/raw") / f"{artifact.stem}.evaluation.v1.json"
    html_path = audit_html or Path("artifacts/audit") / f"{artifact.stem}.html"
    try:
        service = _evaluate_service(
            manifest=manifest,
            process_policy=process_policy,
            crisis_policy=crisis_policy,
            resource_policy=resource_policy,
            evaluation_policy=evaluation_policy,
        )
        result = service.run(artifact, output_path=raw_path)
        write_static_audit(result, html_path)
    except (OSError, UnicodeError, ValueError) as exc:
        _fail(exc)
    typer.echo("EVALUATION COMPLETE")
    typer.echo(f"Case: {result.case_id}")
    typer.echo(
        "Evidence ledger: "
        f"final-only {len(result.final_answer_findings)}, "
        f"trajectory-aware {len(result.trajectory_findings)}"
    )
    typer.echo(f"Raw JSON: {raw_path}")
    typer.echo(f"Audit HTML: {html_path}")


@app.command()
def replay(
    artifact: Annotated[Path, typer.Argument(help="Canonical frozen trajectory JSON.")],
) -> None:
    """Verify and reconstruct one artifact without model, network, or wall clock."""
    try:
        result = replay_artifact(artifact)
    except (OSError, UnicodeError, ValueError) as exc:
        _fail(exc)
    typer.echo("REPLAY VERIFIED")
    typer.echo(f"Canonical hash: {result.canonical_hash}")
    typer.echo(f"Trajectory: {result.trajectory.trajectory_id}")
    typer.echo(f"Turns: {len(result.trajectory.turns)}")


@app.command()
def benchmark(
    manifest: Annotated[
        Path,
        typer.Option("--manifest", help="Ordered frozen benchmark manifest."),
    ],
    output: Annotated[
        Path,
        typer.Option("--output", help="Deterministic raw benchmark JSONL path."),
    ] = Path("artifacts/raw/benchmark.v1.jsonl"),
    trajectory_dir: Annotated[
        Path,
        typer.Option(
            "--trajectory-dir", help="Canonical trajectory artifact directory."
        ),
    ] = Path("benchmarks/trajectories"),
    gold_dir: Annotated[
        Path,
        typer.Option("--gold-dir", help="Frozen comparison-data directory."),
    ] = Path("benchmarks") / "gold",
    process_policy: Annotated[
        Path, typer.Option("--process-policy", help="Process policy registry.")
    ] = DEFAULT_PROCESS_POLICY,
    crisis_policy: Annotated[
        Path, typer.Option("--crisis-policy", help="Crisis policy registry.")
    ] = DEFAULT_CRISIS_POLICY,
    resource_policy: Annotated[
        Path, typer.Option("--resource-policy", help="Resource policy registry.")
    ] = DEFAULT_RESOURCE_POLICY,
    evaluation_policy: Annotated[
        Path,
        typer.Option("--evaluation-policy", help="Offline observation registry."),
    ] = DEFAULT_EVALUATION_POLICY,
    verification_output: Annotated[
        Path,
        typer.Option(
            "--verification-output", help="Deterministic replay/failure JSONL path."
        ),
    ] = Path("artifacts/raw/verification.v1.jsonl"),
    summary_json: Annotated[
        Path,
        typer.Option("--summary-json", help="Canonical derived summary JSON path."),
    ] = Path("artifacts/summary/benchmark.v1.summary.json"),
    summary_markdown: Annotated[
        Path,
        typer.Option(
            "--summary-markdown", help="Deterministic derived summary Markdown path."
        ),
    ] = Path("artifacts/summary/benchmark.v1.summary.md"),
    failure_fixture_dir: Annotated[
        Path,
        typer.Option(
            "--failure-fixture-dir", help="Frozen invalid artifact fixture directory."
        ),
    ] = Path("benchmarks/failure_fixtures"),
) -> None:
    """Write benchmark/verification raw evidence and derived summaries."""
    try:
        service = RunBenchmark.from_paths(
            benchmark_manifest_path=manifest,
            process_policy_path=process_policy,
            crisis_policy_path=crisis_policy,
            resource_policy_path=resource_policy,
            evaluation_policy_path=evaluation_policy,
        )
        result = service.run(
            trajectory_dir=trajectory_dir,
            gold_dir=gold_dir,
            output_path=output,
            failure_fixture_dir=failure_fixture_dir,
            report_paths=BenchmarkReportPaths(
                verification_raw=verification_output,
                summary_json=summary_json,
                summary_markdown=summary_markdown,
            ),
        )
    except (OSError, UnicodeError, ValueError) as exc:
        _fail(exc)
    typer.echo("BENCHMARK COMPLETE")
    typer.echo(f"Cases: {len(result.records)}")
    typer.echo(f"Raw JSONL: {result.output_path}")
    typer.echo(f"Verification JSONL: {verification_output}")
    typer.echo(f"Summary JSON: {summary_json}")
    typer.echo(f"Summary Markdown: {summary_markdown}")


def main() -> None:
    """Run the command-line application."""
    app()
