"""Ordered benchmark execution with post-evaluation gold comparison."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Annotated, Literal, Protocol, Self

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

from careloop.application.evaluate_trajectory import (
    EvaluateTrajectory,
    load_benchmark_manifest,
)
from careloop.artifacts import canonical_json_bytes
from careloop.domain import BenchmarkManifest, Finding, Trajectory
from careloop.evaluation import TrajectoryEvaluationResult


def _non_blank(value: str) -> str:
    if not value.strip():
        raise ValueError("must not be empty or whitespace")
    return value


NonBlank = Annotated[str, AfterValidator(_non_blank)]


class BenchmarkResultModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class PrimaryDifference(BenchmarkResultModel):
    dimension: NonBlank
    good_observation: NonBlank
    bad_observation: NonBlank
    evidence_turn_ids: Annotated[tuple[NonBlank, ...], Field(min_length=1)]


class GoldCase(BenchmarkResultModel):
    gold_schema_version: Literal["v1"]
    case_id: NonBlank
    pair_id: NonBlank
    variant: Literal["good", "bad"]
    observable_findings: Annotated[tuple[Finding, ...], Field(min_length=1)]
    single_primary_difference: PrimaryDifference

    @model_validator(mode="after")
    def validate_unique_rule_ids(self) -> Self:
        rule_ids = tuple(finding.rule_id for finding in self.observable_findings)
        if len(set(rule_ids)) != len(rule_ids):
            raise ValueError("gold rule_id values must be unique per case")
        return self


class FindingComparison(BenchmarkResultModel):
    rule_id: NonBlank
    actual_finding_id: str | None
    gold_finding_id: NonBlank
    actual_outcome: Literal["present", "absent", "uncertain"] | None
    gold_outcome: Literal["present", "absent", "uncertain"]
    outcome_matches: bool
    evidence_turn_ids_match: bool
    source_ids_match: bool
    evaluator_version_matches: bool
    matches: bool

    @model_validator(mode="after")
    def validate_match_derivation(self) -> Self:
        expected = (
            self.outcome_matches
            and self.evidence_turn_ids_match
            and self.source_ids_match
            and self.evaluator_version_matches
        )
        if self.matches != expected:
            raise ValueError("matches must derive from comparison fields")
        return self


class BenchmarkRecord(BenchmarkResultModel):
    record_schema_version: Literal["v1"]
    benchmark_version: Literal["v1"]
    case_id: NonBlank
    pair_id: NonBlank
    variant: Literal["good", "bad"]
    evaluation: TrajectoryEvaluationResult
    single_primary_difference: PrimaryDifference
    comparisons: Annotated[tuple[FindingComparison, ...], Field(min_length=1)]
    all_expected_findings_match: bool

    @model_validator(mode="after")
    def validate_case_match_derivation(self) -> Self:
        if self.all_expected_findings_match != all(
            comparison.matches for comparison in self.comparisons
        ):
            raise ValueError("case match must derive from finding comparisons")
        return self

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self)


class TrajectoryEvaluationService(Protocol):
    @property
    def as_of(self) -> date: ...

    def run(
        self,
        path: str | Path,
        *,
        output_path: str | Path | None = None,
    ) -> TrajectoryEvaluationResult: ...


GoldLoader = Callable[[Path, Trajectory], GoldCase]


@dataclass(frozen=True, slots=True)
class BenchmarkRunResult:
    records: tuple[BenchmarkRecord, ...]
    raw_bytes: bytes
    output_path: Path


def load_gold_case(path: Path, trajectory: Trajectory) -> GoldCase:
    gold = GoldCase.model_validate_json(path.read_text(encoding="utf-8"))
    for finding in gold.observable_findings:
        trajectory.validate_finding(finding)
    return gold


def _compare_findings(
    actual_findings: tuple[Finding, ...], gold_findings: tuple[Finding, ...]
) -> tuple[FindingComparison, ...]:
    actual_by_rule: dict[str, Finding] = {}
    for finding in actual_findings:
        if finding.rule_id in actual_by_rule:
            raise ValueError(f"duplicate actual rule_id: {finding.rule_id}")
        actual_by_rule[finding.rule_id] = finding
    comparisons: list[FindingComparison] = []
    for expected in gold_findings:
        actual = actual_by_rule.get(expected.rule_id)
        outcome_matches = actual is not None and actual.outcome == expected.outcome
        evidence_matches = actual is not None and actual.turn_ids == expected.turn_ids
        source_matches = actual is not None and actual.source_ids == expected.source_ids
        version_matches = (
            actual is not None
            and actual.evaluator_version == expected.evaluator_version
        )
        comparisons.append(
            FindingComparison(
                rule_id=expected.rule_id,
                actual_finding_id=actual.finding_id if actual else None,
                gold_finding_id=expected.finding_id,
                actual_outcome=actual.outcome if actual else None,
                gold_outcome=expected.outcome,
                outcome_matches=outcome_matches,
                evidence_turn_ids_match=evidence_matches,
                source_ids_match=source_matches,
                evaluator_version_matches=version_matches,
                matches=(
                    outcome_matches
                    and evidence_matches
                    and source_matches
                    and version_matches
                ),
            )
        )
    return tuple(comparisons)


class RunBenchmark:
    """Evaluate in manifest order and load gold only after each actual result."""

    def __init__(
        self,
        *,
        evaluator: TrajectoryEvaluationService,
        manifest: BenchmarkManifest,
        gold_loader: GoldLoader = load_gold_case,
    ) -> None:
        if evaluator.as_of != manifest.as_of:
            raise ValueError("evaluator as_of must match benchmark manifest")
        self._evaluator = evaluator
        self._manifest = manifest
        self._gold_loader = gold_loader

    @classmethod
    def from_paths(
        cls,
        *,
        benchmark_manifest_path: str | Path,
        process_policy_path: str | Path,
        crisis_policy_path: str | Path,
        resource_policy_path: str | Path,
        evaluation_policy_path: str | Path,
    ) -> Self:
        manifest = load_benchmark_manifest(benchmark_manifest_path)
        evaluator = EvaluateTrajectory.from_paths(
            benchmark_manifest_path=benchmark_manifest_path,
            process_policy_path=process_policy_path,
            crisis_policy_path=crisis_policy_path,
            resource_policy_path=resource_policy_path,
            evaluation_policy_path=evaluation_policy_path,
        )
        return cls(evaluator=evaluator, manifest=manifest)

    def run(
        self,
        *,
        trajectory_dir: str | Path,
        gold_dir: str | Path,
        output_path: str | Path,
    ) -> BenchmarkRunResult:
        trajectory_root = Path(trajectory_dir)
        gold_root = Path(gold_dir)
        records: list[BenchmarkRecord] = []
        for case_id in self._manifest.case_ids:
            actual = self._evaluator.run(trajectory_root / f"{case_id}.json")
            if actual.case_id != case_id:
                raise ValueError(
                    "artifact case_id mismatch: "
                    f"expected {case_id}, got {actual.case_id}"
                )
            gold = self._gold_loader(gold_root / f"{case_id}.json", actual.trajectory)
            if gold.case_id != case_id:
                raise ValueError(
                    f"gold case_id mismatch: expected {case_id}, got {gold.case_id}"
                )
            comparisons = _compare_findings(
                actual.trajectory_findings, gold.observable_findings
            )
            records.append(
                BenchmarkRecord(
                    record_schema_version="v1",
                    benchmark_version=self._manifest.benchmark_version,
                    case_id=case_id,
                    pair_id=gold.pair_id,
                    variant=gold.variant,
                    evaluation=actual,
                    single_primary_difference=gold.single_primary_difference,
                    comparisons=comparisons,
                    all_expected_findings_match=all(
                        comparison.matches for comparison in comparisons
                    ),
                )
            )
        raw_bytes = b"\n".join(record.canonical_bytes() for record in records) + b"\n"
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw_bytes)
        return BenchmarkRunResult(
            records=tuple(records), raw_bytes=raw_bytes, output_path=destination
        )
