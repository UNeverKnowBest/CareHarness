"""Pure raw-JSONL to summary derivation with no evaluator or policy logic."""

from collections import defaultdict
from collections.abc import Callable, Iterable
from pathlib import Path

from pydantic import BaseModel

from careloop.artifacts import canonical_json_bytes
from careloop.reporting.models import (
    BenchmarkRecord,
    BenchmarkSummary,
    FindingComparison,
    MetricId,
    SummaryMetric,
    VerificationRecord,
)

METRIC_IDS: tuple[MetricId, ...] = (
    "case_level_rule_agreement",
    "matched_pair_discrimination",
    "final_only_missed_process_violations",
    "evidence_localization",
    "crisis_action_agreement",
    "normal_flow_suppression",
    "resource_locale_version_integrity",
    "replay_agreement",
    "invalid_artifact_rejection",
)

PROCESS_RULE_PREFIXES = ("session.", "cbt.", "mi.")
CRISIS_ACTION_RULE_IDS = frozenset(
    {
        "safety.ambiguous_override_recorded",
        "safety.emergency_override_recorded",
    }
)
RESOURCE_RULE_ID = "safety.resource_locale_version_integrity"
FAILURE_EVIDENCE_ORDER = (
    "duplicate_turn_id",
    "hash_mismatch",
    "invalid_finding_turn",
    "unknown_schema",
)
EXPECTED_CASE_ORDER = tuple(
    f"p{pair_number}-{variant}"
    for pair_number in range(1, 9)
    for variant in ("good", "bad")
)
LIMITATIONS = (
    "Synthetic frozen artifacts only; counts are not estimates of real-world or "
    "clinical performance.",
    "No metric is an aggregate quality, safety, risk, treatment, or proficiency score.",
    "Case counts are descriptive regression evidence; no statistical significance "
    "or population generalization is claimed.",
)


def _load_canonical_jsonl[ModelT: BaseModel](
    path: str | Path,
    model_type: type[ModelT],
    *,
    label: str,
) -> tuple[ModelT, ...]:
    raw = Path(path).read_bytes()
    if not raw.endswith(b"\n") or b"\r" in raw:
        raise ValueError(f"{label} raw JSONL must use LF and one final newline")
    lines = raw[:-1].split(b"\n")
    if not lines or any(not line for line in lines):
        raise ValueError(f"{label} raw JSONL must contain non-empty records")
    records: list[ModelT] = []
    for index, line in enumerate(lines, start=1):
        record = model_type.model_validate_json(line)
        if canonical_json_bytes(record) != line:
            raise ValueError(f"{label} raw record {index} is not canonical")
        records.append(record)
    return tuple(records)


def load_benchmark_records(path: str | Path) -> tuple[BenchmarkRecord, ...]:
    records = _load_canonical_jsonl(path, BenchmarkRecord, label="benchmark")
    if len(records) != 16:
        raise ValueError("benchmark raw must contain exactly 16 manifest cases")
    case_ids = tuple(record.case_id for record in records)
    if len(set(case_ids)) != len(case_ids):
        raise ValueError("benchmark raw case IDs must be unique")
    if case_ids != EXPECTED_CASE_ORDER:
        raise ValueError("benchmark raw must retain frozen manifest order")
    return records


def load_verification_records(path: str | Path) -> tuple[VerificationRecord, ...]:
    records = _load_canonical_jsonl(path, VerificationRecord, label="verification")
    if len(records) != 20:
        raise ValueError("verification raw must contain 16 replay and four failures")
    return records


def _metric(
    metric_id: MetricId,
    evidence: Iterable[tuple[str, bool]],
) -> SummaryMetric:
    ordered = tuple(evidence)
    return SummaryMetric(
        metric_id=metric_id,
        satisfied_count=sum(satisfied for _, satisfied in ordered),
        applicable_count=len(ordered),
        satisfied_evidence_ids=tuple(
            evidence_id for evidence_id, satisfied in ordered if satisfied
        ),
        unsatisfied_evidence_ids=tuple(
            evidence_id for evidence_id, satisfied in ordered if not satisfied
        ),
    )


def _validate_inputs(
    benchmark_records: tuple[BenchmarkRecord, ...],
    verification_records: tuple[VerificationRecord, ...],
) -> None:
    versions = {record.benchmark_version for record in benchmark_records}
    dates = {record.evaluation.as_of.isoformat() for record in benchmark_records}
    if len(versions) != 1 or len(dates) != 1:
        raise ValueError("benchmark raw must use one benchmark version and as_of")
    replay = tuple(
        record
        for record in verification_records
        if record.verification_kind == "replay_agreement"
    )
    failures = tuple(
        record
        for record in verification_records
        if record.verification_kind == "invalid_artifact_rejection"
    )
    if tuple(record.evidence_id for record in replay) != tuple(
        record.case_id for record in benchmark_records
    ):
        raise ValueError("replay verification order must match benchmark cases")
    if tuple(record.evidence_id for record in failures) != FAILURE_EVIDENCE_ORDER:
        raise ValueError("failure verification order does not match frozen fixtures")


def _pair_evidence(
    records: tuple[BenchmarkRecord, ...],
) -> tuple[tuple[str, bool], ...]:
    pairs: dict[str, list[BenchmarkRecord]] = defaultdict(list)
    for record in records:
        pairs[record.pair_id].append(record)
    evidence: list[tuple[str, bool]] = []
    for pair_id, pair_records in pairs.items():
        variants = {record.variant: record for record in pair_records}
        good = variants.get("good")
        bad = variants.get("bad")
        satisfied = False
        if good is not None and bad is not None and len(pair_records) == 2:
            good_outcomes = {
                comparison.rule_id: comparison.actual_outcome
                for comparison in good.comparisons
            }
            bad_outcomes = {
                comparison.rule_id: comparison.actual_outcome
                for comparison in bad.comparisons
            }
            shared_rules = good_outcomes.keys() & bad_outcomes.keys()
            satisfied = (
                good.all_expected_findings_match
                and bad.all_expected_findings_match
                and good.single_primary_difference.dimension
                == bad.single_primary_difference.dimension
                and any(
                    good_outcomes[rule_id] != bad_outcomes[rule_id]
                    for rule_id in shared_rules
                )
            )
        evidence.append((pair_id, satisfied))
    return tuple(evidence)


def _comparison_evidence(
    records: tuple[BenchmarkRecord, ...],
    predicate: Callable[[str], bool],
    outcome: Callable[[FindingComparison], bool],
) -> tuple[tuple[str, bool], ...]:
    evidence: list[tuple[str, bool]] = []
    for record in records:
        for comparison in record.comparisons:
            if predicate(comparison.rule_id):
                evidence.append(
                    (
                        f"{record.case_id}:{comparison.rule_id}",
                        outcome(comparison),
                    )
                )
    return tuple(evidence)


def derive_benchmark_summary(
    benchmark_raw_path: str | Path,
    verification_raw_path: str | Path,
) -> BenchmarkSummary:
    benchmark_records = load_benchmark_records(benchmark_raw_path)
    verification_records = load_verification_records(verification_raw_path)
    _validate_inputs(benchmark_records, verification_records)

    missed_process: list[tuple[str, bool]] = []
    suppression: list[tuple[str, bool]] = []
    for record in benchmark_records:
        final_by_rule = {
            finding.rule_id: finding
            for finding in record.evaluation.final_answer_findings
        }
        for finding in record.evaluation.trajectory_findings:
            if (
                finding.rule_id.startswith(PROCESS_RULE_PREFIXES)
                and finding.outcome == "present"
            ):
                final = final_by_rule.get(finding.rule_id)
                missed_process.append(
                    (
                        f"{record.case_id}:{finding.rule_id}",
                        final is None or final.outcome != "present",
                    )
                )
        for event in record.evaluation.trajectory.safety_events:
            if event.requires_override:
                suppression.append(
                    (
                        f"{record.case_id}:{event.event_id}",
                        event.normal_flow_suppressed,
                    )
                )

    replay = tuple(
        (record.evidence_id, record.matches)
        for record in verification_records
        if record.verification_kind == "replay_agreement"
    )
    failures = tuple(
        (record.evidence_id, record.matches)
        for record in verification_records
        if record.verification_kind == "invalid_artifact_rejection"
    )
    metrics = (
        _metric(
            METRIC_IDS[0],
            (
                (record.case_id, record.all_expected_findings_match)
                for record in benchmark_records
            ),
        ),
        _metric(METRIC_IDS[1], _pair_evidence(benchmark_records)),
        _metric(METRIC_IDS[2], missed_process),
        _metric(
            METRIC_IDS[3],
            _comparison_evidence(
                benchmark_records,
                lambda _rule_id: True,
                lambda comparison: comparison.evidence_turn_ids_match,
            ),
        ),
        _metric(
            METRIC_IDS[4],
            _comparison_evidence(
                benchmark_records,
                CRISIS_ACTION_RULE_IDS.__contains__,
                lambda comparison: comparison.matches,
            ),
        ),
        _metric(METRIC_IDS[5], suppression),
        _metric(
            METRIC_IDS[6],
            _comparison_evidence(
                benchmark_records,
                lambda rule_id: rule_id == RESOURCE_RULE_ID,
                lambda comparison: comparison.matches,
            ),
        ),
        _metric(METRIC_IDS[7], replay),
        _metric(METRIC_IDS[8], failures),
    )
    return BenchmarkSummary(
        summary_schema_version="v1",
        benchmark_version=benchmark_records[0].benchmark_version,
        as_of=benchmark_records[0].evaluation.as_of.isoformat(),
        metrics=metrics,
        limitations=LIMITATIONS,
    )


def render_summary_markdown(summary: BenchmarkSummary) -> bytes:
    lines = [
        "# CareLoop Harness Synthetic Benchmark Summary",
        "",
        "> Descriptive regression evidence only; no aggregate score or "
        "statistical inference.",
        "",
        f"- Benchmark version: `{summary.benchmark_version}`",
        f"- Frozen as-of date: `{summary.as_of}`",
        "",
        "| Metric | Satisfied / applicable | Evidence IDs | Scope |",
        "|---|---:|---|---|",
    ]
    for metric in summary.metrics:
        satisfied = ", ".join(metric.satisfied_evidence_ids) or "none"
        unsatisfied = ", ".join(metric.unsatisfied_evidence_ids)
        evidence = satisfied
        if unsatisfied:
            evidence = f"matched: {satisfied}; unmatched: {unsatisfied}"
        lines.append(
            f"| `{metric.metric_id}` | {metric.satisfied_count} / "
            f"{metric.applicable_count} | {evidence} | "
            "synthetic / frozen / non-clinical |"
        )
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {limitation}" for limitation in summary.limitations)
    lines.append("")
    return "\n".join(lines).encode("utf-8")


def write_benchmark_summary(
    benchmark_raw_path: str | Path,
    verification_raw_path: str | Path,
    *,
    summary_json_path: str | Path,
    summary_markdown_path: str | Path,
) -> BenchmarkSummary:
    summary = derive_benchmark_summary(benchmark_raw_path, verification_raw_path)
    json_destination = Path(summary_json_path)
    markdown_destination = Path(summary_markdown_path)
    json_destination.parent.mkdir(parents=True, exist_ok=True)
    markdown_destination.parent.mkdir(parents=True, exist_ok=True)
    json_destination.write_bytes(summary.canonical_bytes())
    markdown_destination.write_bytes(render_summary_markdown(summary))
    return summary
