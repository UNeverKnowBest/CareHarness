import json
from pathlib import Path

import pytest

from careloop.application import BenchmarkReportPaths, RunBenchmark
from careloop.reporting import (
    METRIC_IDS,
    derive_benchmark_summary,
    load_benchmark_records,
    render_summary_markdown,
)

ROOT = Path(__file__).parents[2]
MANIFEST_PATH = ROOT / "benchmarks" / "manifest.v1.json"
TRAJECTORY_ROOT = ROOT / "benchmarks" / "trajectories"
GOLD_ROOT = ROOT / "benchmarks" / "gold"
FAILURE_ROOT = ROOT / "benchmarks" / "failure_fixtures"
PROCESS_POLICY_PATH = ROOT / "policies" / "process.v1.json"
CRISIS_POLICY_PATH = ROOT / "policies" / "crisis.v1.json"
RESOURCE_POLICY_PATH = ROOT / "policies" / "resources.v1.json"
EVALUATION_POLICY_PATH = ROOT / "policies" / "evaluation.v1.json"


def _run_full_report(tmp_path: Path):  # type: ignore[no-untyped-def]
    runner = RunBenchmark.from_paths(
        benchmark_manifest_path=MANIFEST_PATH,
        process_policy_path=PROCESS_POLICY_PATH,
        crisis_policy_path=CRISIS_POLICY_PATH,
        resource_policy_path=RESOURCE_POLICY_PATH,
        evaluation_policy_path=EVALUATION_POLICY_PATH,
    )
    report_paths = BenchmarkReportPaths(
        verification_raw=tmp_path / "verification.v1.jsonl",
        summary_json=tmp_path / "benchmark.v1.summary.json",
        summary_markdown=tmp_path / "benchmark.v1.summary.md",
    )
    result = runner.run(
        trajectory_dir=TRAJECTORY_ROOT,
        gold_dir=GOLD_ROOT,
        output_path=tmp_path / "benchmark.v1.jsonl",
        failure_fixture_dir=FAILURE_ROOT,
        report_paths=report_paths,
    )
    return result, report_paths


def test_full_report_is_derived_from_raw_with_only_allowed_metrics(
    tmp_path: Path,
) -> None:
    result, report_paths = _run_full_report(tmp_path)

    assert len(result.records) == 16
    assert len(result.verification_records) == 20
    summary = derive_benchmark_summary(
        result.output_path, report_paths.verification_raw
    )
    assert tuple(metric.metric_id for metric in summary.metrics) == METRIC_IDS
    assert {
        metric.metric_id: (metric.satisfied_count, metric.applicable_count)
        for metric in summary.metrics
    } == {
        "case_level_rule_agreement": (16, 16),
        "matched_pair_discrimination": (8, 8),
        "final_only_missed_process_violations": (5, 5),
        "evidence_localization": (16, 16),
        "crisis_action_agreement": (4, 4),
        "normal_flow_suppression": (4, 4),
        "resource_locale_version_integrity": (2, 2),
        "replay_agreement": (16, 16),
        "invalid_artifact_rejection": (4, 4),
    }
    assert report_paths.summary_json.read_bytes() == summary.canonical_bytes()
    assert report_paths.summary_markdown.read_bytes() == render_summary_markdown(
        summary
    )

    payload = json.loads(report_paths.summary_json.read_text(encoding="utf-8"))
    assert "aggregate_score" not in payload
    assert "percentage" not in payload
    markdown = report_paths.summary_markdown.read_text(encoding="utf-8")
    assert markdown.count("synthetic / frozen / non-clinical") == len(METRIC_IDS)
    assert "%" not in markdown
    assert "statistically significant" not in markdown.casefold()


def test_recomputing_summary_from_unchanged_raw_is_byte_identical(
    tmp_path: Path,
) -> None:
    result, report_paths = _run_full_report(tmp_path)
    first_json = report_paths.summary_json.read_bytes()
    first_markdown = report_paths.summary_markdown.read_bytes()

    summary = derive_benchmark_summary(
        result.output_path, report_paths.verification_raw
    )

    assert summary.canonical_bytes() == first_json
    assert render_summary_markdown(summary) == first_markdown


def test_report_rejects_noncanonical_benchmark_raw(tmp_path: Path) -> None:
    malformed = tmp_path / "benchmark.jsonl"
    first_line = (
        (ROOT / "artifacts" / "raw" / "benchmark.v1.jsonl").read_bytes().splitlines()[0]
    )
    malformed.write_bytes(first_line + b" \n")

    with pytest.raises(ValueError, match="canonical"):
        load_benchmark_records(malformed)


def test_report_rejects_benchmark_raw_outside_frozen_manifest_order(
    tmp_path: Path,
) -> None:
    source_lines = (
        (ROOT / "artifacts" / "raw" / "benchmark.v1.jsonl").read_bytes().splitlines()
    )
    reordered = tmp_path / "reordered.jsonl"
    reordered.write_bytes(
        b"\n".join((source_lines[1], source_lines[0], *source_lines[2:])) + b"\n"
    )

    with pytest.raises(ValueError, match="manifest order"):
        load_benchmark_records(reordered)


def test_verification_raw_records_expected_failure_reasons(tmp_path: Path) -> None:
    result, _ = _run_full_report(tmp_path)
    failures = {
        record.evidence_id: record.observed_observation
        for record in result.verification_records
        if record.verification_kind == "invalid_artifact_rejection"
    }

    assert failures == {
        "duplicate_turn_id": "schema_validation_error",
        "hash_mismatch": "artifact_hash_mismatch",
        "invalid_finding_turn": "finding_reference_error",
        "unknown_schema": "schema_validation_error",
    }
    assert all(record.matches for record in result.verification_records)
