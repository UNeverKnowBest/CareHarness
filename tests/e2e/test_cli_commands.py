import json
from pathlib import Path

from typer.testing import CliRunner

from careloop.cli import app

ROOT = Path(__file__).parents[2]
TRAJECTORY_ROOT = ROOT / "benchmarks" / "trajectories"

runner = CliRunner()


def test_evaluate_command_writes_raw_result_and_static_audit(tmp_path: Path) -> None:
    raw_path = tmp_path / "p1-bad.json"
    audit_path = tmp_path / "p1-bad.html"

    result = runner.invoke(
        app,
        [
            "evaluate",
            str(TRAJECTORY_ROOT / "p1-bad.json"),
            "--manifest",
            str(ROOT / "benchmarks" / "manifest.v1.json"),
            "--output",
            str(raw_path),
            "--audit-html",
            str(audit_path),
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert "EVALUATION COMPLETE" in result.stdout
    assert "Evidence ledger: final-only 10, trajectory-aware 10" in result.stdout
    assert raw_path.is_file()
    assert audit_path.is_file()
    assert json.loads(raw_path.read_text(encoding="utf-8"))["case_id"] == "p1-bad"


def test_replay_command_verifies_hash_without_writing_output() -> None:
    result = runner.invoke(app, ["replay", str(TRAJECTORY_ROOT / "p2-good.json")])

    assert result.exit_code == 0
    assert "REPLAY VERIFIED" in result.stdout
    assert "sha256:" in result.stdout
    assert "p2-synthetic-matched-trajectory" in result.stdout


def test_benchmark_command_writes_sixteen_ordered_raw_records(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "benchmark.v1.jsonl"
    verification_path = tmp_path / "verification.v1.jsonl"
    summary_json = tmp_path / "benchmark.v1.summary.json"
    summary_markdown = tmp_path / "benchmark.v1.summary.md"

    result = runner.invoke(
        app,
        [
            "benchmark",
            "--manifest",
            str(ROOT / "benchmarks" / "manifest.v1.json"),
            "--output",
            str(output_path),
            "--verification-output",
            str(verification_path),
            "--summary-json",
            str(summary_json),
            "--summary-markdown",
            str(summary_markdown),
            "--failure-fixture-dir",
            str(ROOT / "benchmarks" / "failure_fixtures"),
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert "BENCHMARK COMPLETE" in result.stdout
    assert "Cases: 16" in result.stdout
    assert len(output_path.read_bytes().splitlines()) == 16
    assert len(verification_path.read_bytes().splitlines()) == 20
    assert summary_json.is_file()
    assert summary_markdown.is_file()
    assert f"Summary JSON: {summary_json}" in result.stdout
    assert f"Summary Markdown: {summary_markdown}" in result.stdout


def test_invalid_artifact_returns_application_error_exit_one() -> None:
    result = runner.invoke(
        app,
        [
            "evaluate",
            str(ROOT / "benchmarks" / "failure_fixtures" / "hash_mismatch.json"),
            "--manifest",
            str(ROOT / "benchmarks" / "manifest.v1.json"),
        ],
    )

    assert result.exit_code == 1
    assert "artifact hash mismatch" in result.stderr
