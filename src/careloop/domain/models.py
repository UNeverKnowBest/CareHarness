"""Frozen Day 1 domain models and aggregate validation."""

from datetime import date
from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator


def _non_blank(value: str) -> str:
    if not value.strip():
        raise ValueError("must not be empty or whitespace")
    return value


NonBlankStr = Annotated[str, AfterValidator(_non_blank)]
NonEmptyStrings = Annotated[tuple[NonBlankStr, ...], Field(min_length=1)]
NonEmptyTurns = Annotated[tuple["Turn", ...], Field(min_length=1)]
SupportedVersion = Literal["v1"]


class DomainModel(BaseModel):
    """Base configuration shared by every public Day 1 model."""

    model_config = ConfigDict(extra="forbid")


class SafetyAction(StrEnum):
    """System actions emitted by the safety boundary."""

    CONTINUE_SUPPORT = "continue_support"
    PAUSE_AND_CLARIFY_NOW = "pause_and_clarify_now"
    CONNECT_HUMAN_HELP_NOW = "connect_human_help_now"
    SEEK_EMERGENCY_HELP_NOW = "seek_emergency_help_now"


class Turn(DomainModel):
    """One ordered synthetic trajectory turn."""

    turn_id: NonBlankStr
    sequence: Annotated[int, Field(ge=0)]
    role: Literal["user", "assistant"]
    text: str


class ProcessMarker(DomainModel):
    """Observable process evidence attached to one turn."""

    marker_id: NonBlankStr
    turn_id: NonBlankStr
    marker_type: NonBlankStr
    value: NonBlankStr
    source_ids: NonEmptyStrings
    process_policy_version: SupportedVersion


class SafetyEvent(DomainModel):
    """A typed system safety action recorded in a trajectory."""

    event_id: NonBlankStr
    triggering_turn_ids: NonEmptyStrings
    action: SafetyAction
    requires_override: bool
    normal_flow_suppressed: bool
    source_ids: NonEmptyStrings
    resource_ids: tuple[NonBlankStr, ...]
    crisis_policy_version: SupportedVersion

    @model_validator(mode="after")
    def validate_override_suppression(self) -> Self:
        if self.requires_override and not self.normal_flow_suppressed:
            raise ValueError(
                "normal_flow_suppressed must be true when requires_override is true"
            )
        return self


class Finding(DomainModel):
    """Evaluator evidence about observable trajectory behavior."""

    finding_id: NonBlankStr
    rule_id: NonBlankStr
    outcome: Literal["present", "absent", "uncertain"]
    turn_ids: NonEmptyStrings
    source_ids: NonEmptyStrings
    evaluator_version: SupportedVersion


class CrisisResource(DomainModel):
    """Allowlisted, source-linked synthetic resource registry entry."""

    resource_id: NonBlankStr
    name: NonBlankStr
    jurisdiction: NonBlankStr
    contact: NonBlankStr
    source_url: NonBlankStr
    is_allowlisted: bool
    verified_on: date
    expires_on: date
    resource_registry_version: SupportedVersion

    @model_validator(mode="after")
    def validate_registry_constraints(self) -> Self:
        if not self.is_allowlisted:
            raise ValueError("is_allowlisted must be true")
        if self.expires_on < self.verified_on:
            raise ValueError("expires_on must not precede verified_on")
        return self


class Trajectory(DomainModel):
    """Ordered trajectory aggregate with embedded marker and safety evidence."""

    trajectory_schema_version: SupportedVersion
    trajectory_id: NonBlankStr
    turns: NonEmptyTurns
    process_markers: tuple[ProcessMarker, ...]
    safety_events: tuple[SafetyEvent, ...]

    @model_validator(mode="after")
    def validate_aggregate(self) -> Self:
        turn_ids = tuple(turn.turn_id for turn in self.turns)
        if len(set(turn_ids)) != len(turn_ids):
            raise ValueError("turn_id values must be unique within a trajectory")

        sequences = tuple(turn.sequence for turn in self.turns)
        if any(
            current <= previous for previous, current in zip(sequences, sequences[1:])
        ):
            raise ValueError("turn sequence must be strictly increasing")

        known_turn_ids = set(turn_ids)
        for marker in self.process_markers:
            if marker.turn_id not in known_turn_ids:
                raise ValueError(
                    f"process marker references unknown turn_id: {marker.turn_id}"
                )

        for event in self.safety_events:
            missing = set(event.triggering_turn_ids) - known_turn_ids
            if missing:
                missing_ids = ", ".join(sorted(missing))
                raise ValueError(
                    f"safety event references unknown turn_id: {missing_ids}"
                )
        return self

    def validate_finding(self, finding: Finding) -> None:
        """Validate standalone finding evidence against this trajectory."""
        known_turn_ids = {turn.turn_id for turn in self.turns}
        missing = set(finding.turn_ids) - known_turn_ids
        if missing:
            missing_ids = ", ".join(sorted(missing))
            raise ValueError(f"finding references unknown turn_id: {missing_ids}")


class EvaluationManifest(DomainModel):
    """Independent Day 1 schema and policy version selectors."""

    trajectory_schema_version: SupportedVersion
    process_policy_version: SupportedVersion
    ethical_policy_version: SupportedVersion
    crisis_policy_version: SupportedVersion
    resource_registry_version: SupportedVersion
    evaluator_version: SupportedVersion


class BenchmarkManifest(DomainModel):
    """Ordered benchmark case selection at an explicit date."""

    benchmark_version: SupportedVersion
    as_of: date
    case_ids: NonEmptyStrings
    resource_registry_version: SupportedVersion

    @model_validator(mode="after")
    def validate_unique_case_ids(self) -> Self:
        if len(set(self.case_ids)) != len(self.case_ids):
            raise ValueError("case_ids must not contain duplicates")
        return self


class FinalAnswerView(DomainModel):
    """Narrow input boundary for a future final-answer evaluator."""

    text: str
    turn_id: NonBlankStr
