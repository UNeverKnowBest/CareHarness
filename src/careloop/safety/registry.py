"""Strict versioned registries for synthetic crisis and ethical policies."""

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


class SafetyPolicyModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class SafetyPolicySource(SafetyPolicyModel):
    source_id: NonBlank
    title: NonBlank
    locator: NonBlank


class SyntheticSignalRule(SafetyPolicyModel):
    signal_id: NonBlank
    phrases: NonEmptyStrings
    action: SafetyAction
    requires_override: Literal[True]
    source_ids: NonEmptyStrings

    @model_validator(mode="after")
    def validate_override_action(self) -> Self:
        if self.action is SafetyAction.CONTINUE_SUPPORT:
            raise ValueError("a frozen safety signal cannot continue normal support")
        return self


class CrisisPolicyRegistry(SafetyPolicyModel):
    policy_schema_version: Literal["v1"]
    crisis_policy_version: Literal["v1"]
    evaluator_version: Literal["v1"]
    fail_closed_action: SafetyAction
    fail_closed_source_ids: NonEmptyStrings
    sources: Annotated[tuple[SafetyPolicySource, ...], Field(min_length=1)]
    signals: Annotated[tuple[SyntheticSignalRule, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def validate_registry(self) -> Self:
        source_ids = tuple(source.source_id for source in self.sources)
        if len(set(source_ids)) != len(source_ids):
            raise ValueError("source_id values must be unique")
        signal_ids = tuple(signal.signal_id for signal in self.signals)
        if len(set(signal_ids)) != len(signal_ids):
            raise ValueError("signal_id values must be unique")
        known_sources = set(source_ids)
        referenced_sources = set(self.fail_closed_source_ids)
        for signal in self.signals:
            referenced_sources.update(signal.source_ids)
        missing = referenced_sources - known_sources
        if missing:
            raise ValueError(
                f"crisis policy references unknown source: {', '.join(sorted(missing))}"
            )
        if self.fail_closed_action is SafetyAction.CONTINUE_SUPPORT:
            raise ValueError("fail_closed_action cannot continue normal support")
        return self


class EthicalRule(SafetyPolicyModel):
    rule_id: NonBlank
    phrases: NonEmptyStrings
    source_ids: NonEmptyStrings
    only_during_override: bool = False


class EthicalPolicyRegistry(SafetyPolicyModel):
    policy_schema_version: Literal["v1"]
    ethical_policy_version: Literal["v1"]
    evaluator_version: Literal["v1"]
    sources: Annotated[tuple[SafetyPolicySource, ...], Field(min_length=1)]
    rules: Annotated[tuple[EthicalRule, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def validate_registry(self) -> Self:
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
                    f"ethical rule {rule.rule_id} references unknown source: "
                    f"{', '.join(sorted(missing))}"
                )
        return self


def load_crisis_policy(path: str | Path) -> CrisisPolicyRegistry:
    return CrisisPolicyRegistry.model_validate_json(
        Path(path).read_text(encoding="utf-8")
    )


def load_ethical_policy(path: str | Path) -> EthicalPolicyRegistry:
    return EthicalPolicyRegistry.model_validate_json(
        Path(path).read_text(encoding="utf-8")
    )
