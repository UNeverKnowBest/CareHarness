"""Strict immutable raw and derived reporting models."""

from typing import Annotated, Literal, Self

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

from careloop.artifacts import canonical_json_bytes
from careloop.evaluation import TrajectoryEvaluationResult


def _non_blank(value: str) -> str:
    if not value.strip():
        raise ValueError("must not be empty or whitespace")
    return value


NonBlank = Annotated[str, AfterValidator(_non_blank)]


class ReportingModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class PrimaryDifference(ReportingModel):
    dimension: NonBlank
    good_observation: NonBlank
    bad_observation: NonBlank
    evidence_turn_ids: Annotated[tuple[NonBlank, ...], Field(min_length=1)]


class FindingComparison(ReportingModel):
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


class BenchmarkRecord(ReportingModel):
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


VerificationKind = Literal["replay_agreement", "invalid_artifact_rejection"]
VerificationObservation = Literal[
    "canonical_replay_identity",
    "schema_validation_error",
    "artifact_hash_mismatch",
    "finding_reference_error",
    "replay_identity_mismatch",
    "accepted",
    "unexpected_error",
]


class VerificationRecord(ReportingModel):
    verification_schema_version: Literal["v1"]
    verification_kind: VerificationKind
    evidence_id: NonBlank
    expected_observation: VerificationObservation
    observed_observation: VerificationObservation
    canonical_hash: str | None
    matches: bool

    @model_validator(mode="after")
    def validate_verification_derivation(self) -> Self:
        expected_match = self.expected_observation == self.observed_observation
        if self.matches != expected_match:
            raise ValueError("matches must derive from verification observations")
        if self.verification_kind == "replay_agreement":
            if self.expected_observation != "canonical_replay_identity":
                raise ValueError("replay verification requires canonical identity")
            if self.canonical_hash is None:
                raise ValueError("replay verification requires canonical_hash")
        elif self.canonical_hash is not None:
            raise ValueError("invalid-artifact verification has no canonical_hash")
        return self

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self)


MetricId = Literal[
    "case_level_rule_agreement",
    "matched_pair_discrimination",
    "final_only_missed_process_violations",
    "evidence_localization",
    "crisis_action_agreement",
    "normal_flow_suppression",
    "resource_locale_version_integrity",
    "replay_agreement",
    "invalid_artifact_rejection",
]


class SummaryMetric(ReportingModel):
    metric_id: MetricId
    satisfied_count: Annotated[int, Field(ge=0)]
    applicable_count: Annotated[int, Field(ge=0)]
    satisfied_evidence_ids: tuple[NonBlank, ...]
    unsatisfied_evidence_ids: tuple[NonBlank, ...]

    @model_validator(mode="after")
    def validate_counts(self) -> Self:
        if self.satisfied_count > self.applicable_count:
            raise ValueError("satisfied_count cannot exceed applicable_count")
        if len(self.satisfied_evidence_ids) != self.satisfied_count:
            raise ValueError("satisfied evidence count mismatch")
        if (
            len(self.satisfied_evidence_ids) + len(self.unsatisfied_evidence_ids)
            != self.applicable_count
        ):
            raise ValueError("applicable evidence count mismatch")
        all_ids = self.satisfied_evidence_ids + self.unsatisfied_evidence_ids
        if len(set(all_ids)) != len(all_ids):
            raise ValueError("metric evidence IDs must be unique")
        return self


class BenchmarkSummary(ReportingModel):
    summary_schema_version: Literal["v1"]
    benchmark_version: Literal["v1"]
    as_of: str
    metrics: Annotated[tuple[SummaryMetric, ...], Field(min_length=9, max_length=9)]
    limitations: Annotated[tuple[NonBlank, ...], Field(min_length=1)]

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self)
