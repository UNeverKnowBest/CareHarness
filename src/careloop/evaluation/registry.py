"""Strict registry for offline safety-artifact observation rules."""

from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

from careloop.domain import SafetyAction


def _non_blank(value: str) -> str:
    if not value.strip():
        raise ValueError("must not be empty or whitespace")
    return value


NonBlank = Annotated[str, AfterValidator(_non_blank)]
NonEmptyStrings = Annotated[tuple[NonBlank, ...], Field(min_length=1)]


class EvaluationPolicyModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class EvaluationPolicySource(EvaluationPolicyModel):
    source_id: NonBlank
    title: NonBlank
    locator: NonBlank


class SafetyObservationRule(EvaluationPolicyModel):
    rule_id: NonBlank
    kind: Literal["override_action", "resource_integrity"]
    signal_ids: NonEmptyStrings
    expected_action: SafetyAction
    source_ids: NonEmptyStrings

    @model_validator(mode="after")
    def validate_action(self) -> Self:
        if self.expected_action is SafetyAction.CONTINUE_SUPPORT:
            raise ValueError("safety observation cannot expect normal continuation")
        return self


class EvaluationPolicyRegistry(EvaluationPolicyModel):
    policy_schema_version: Literal["v1"]
    evaluator_version: Literal["v1"]
    sources: Annotated[tuple[EvaluationPolicySource, ...], Field(min_length=1)]
    safety_observations: Annotated[
        tuple[SafetyObservationRule, ...], Field(min_length=1)
    ]

    @model_validator(mode="after")
    def validate_registry(self) -> Self:
        source_ids = tuple(source.source_id for source in self.sources)
        if len(set(source_ids)) != len(source_ids):
            raise ValueError("source_id values must be unique")
        rule_ids = tuple(rule.rule_id for rule in self.safety_observations)
        if len(set(rule_ids)) != len(rule_ids):
            raise ValueError("rule_id values must be unique")
        known_sources = set(source_ids)
        for rule in self.safety_observations:
            missing = set(rule.source_ids) - known_sources
            if missing:
                raise ValueError(
                    f"evaluation rule {rule.rule_id} references unknown source: "
                    f"{', '.join(sorted(missing))}"
                )
        return self


def load_evaluation_policy(path: str | Path) -> EvaluationPolicyRegistry:
    return EvaluationPolicyRegistry.model_validate_json(
        Path(path).read_text(encoding="utf-8")
    )
