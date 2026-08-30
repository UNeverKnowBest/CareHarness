"""Validated, versioned metadata for deterministic process evaluation."""

from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

NonBlank = Annotated[str, Field(min_length=1)]
NonEmptyStrings = Annotated[tuple[NonBlank, ...], Field(min_length=1)]
EvaluatorName = Literal["session_shell", "cbt_informed", "mi_inspired"]


class PolicyModel(BaseModel):
    """Strict immutable policy metadata base."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class ProcessSource(PolicyModel):
    source_id: NonBlank
    title: NonBlank
    locator: NonBlank


class TextSignalRule(PolicyModel):
    rule_id: NonBlank
    evaluator: EvaluatorName
    kind: Literal["text_signal"]
    source_ids: NonEmptyStrings
    target_role: Literal["user", "assistant"]
    present_phrases: NonEmptyStrings
    absent_phrases: NonEmptyStrings


class MarkerCountRule(PolicyModel):
    rule_id: NonBlank
    evaluator: EvaluatorName
    kind: Literal["marker_count"]
    source_ids: NonEmptyStrings
    marker_type: NonBlank
    marker_value: NonBlank
    max_count: Annotated[int, Field(ge=0)]


class MarkerTransitionRule(PolicyModel):
    rule_id: NonBlank
    evaluator: EvaluatorName
    kind: Literal["marker_transition"]
    source_ids: NonEmptyStrings
    marker_type: NonBlank
    allowed_values: NonEmptyStrings
    allowed_transitions: Annotated[
        tuple[tuple[NonBlank, NonBlank], ...], Field(min_length=1)
    ]

    @model_validator(mode="after")
    def validate_transition_values(self) -> Self:
        allowed = set(self.allowed_values)
        referenced = {
            value for transition in self.allowed_transitions for value in transition
        }
        if not referenced <= allowed:
            raise ValueError("allowed_transitions reference an unknown allowed value")
        return self


ProcessRule = Annotated[
    TextSignalRule | MarkerCountRule | MarkerTransitionRule,
    Field(discriminator="kind"),
]


class ProcessPolicyRegistry(PolicyModel):
    """Complete executable rule and source registry for process policy v1."""

    policy_schema_version: Literal["v1"]
    process_policy_version: Literal["v1"]
    evaluator_version: Literal["v1"]
    sources: Annotated[tuple[ProcessSource, ...], Field(min_length=1)]
    rules: Annotated[tuple[ProcessRule, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def validate_ids_and_references(self) -> Self:
        source_ids = tuple(source.source_id for source in self.sources)
        if len(set(source_ids)) != len(source_ids):
            raise ValueError("source_id values must be unique")

        rule_ids = tuple(rule.rule_id for rule in self.rules)
        if len(set(rule_ids)) != len(rule_ids):
            raise ValueError("rule_id values must be unique")

        known_sources = set(source_ids)
        for rule in self.rules:
            missing = set(rule.source_ids) - known_sources
            if missing:
                raise ValueError(
                    f"rule {rule.rule_id} references unknown source: "
                    f"{', '.join(sorted(missing))}"
                )
        return self


def load_process_policy(path: str | Path) -> ProcessPolicyRegistry:
    """Load strict local JSON metadata without adding evaluator side effects."""
    return ProcessPolicyRegistry.model_validate_json(
        Path(path).read_text(encoding="utf-8")
    )
