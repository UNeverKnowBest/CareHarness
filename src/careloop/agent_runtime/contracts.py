"""Versioned, provider-neutral contracts for the synthetic agent runtime."""

from enum import StrEnum
from typing import Annotated, Final, Literal, Self

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

from careloop.domain import Turn

MAX_DRAFT_REWRITE_ATTEMPTS: Final[Literal[2]] = 2


def _non_blank(value: str) -> str:
    if not value.strip():
        raise ValueError("must not be empty or whitespace")
    return value


NonBlankStr = Annotated[str, AfterValidator(_non_blank)]
NonEmptyStrings = Annotated[tuple[NonBlankStr, ...], Field(min_length=1)]
Sha256Digest = Annotated[str, Field(pattern=r"^sha256:[0-9a-f]{64}$")]
ContractVersion = Literal["v1"]


class RuntimeContractModel(BaseModel):
    """Strict base for the M8 runtime wire contract."""

    model_config = ConfigDict(extra="forbid")


class SafetyDisposition(StrEnum):
    """System routing states, never clinical classifications of a person."""

    SUPPORT_ALLOWED = "SUPPORT_ALLOWED"
    CLARIFICATION_REQUIRED = "CLARIFICATION_REQUIRED"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
    EMERGENCY_GUIDANCE_REQUIRED = "EMERGENCY_GUIDANCE_REQUIRED"
    SYSTEM_FAILURE = "SYSTEM_FAILURE"


class DraftDecision(StrEnum):
    """Actions available to the pre-release draft gate."""

    ALLOW = "ALLOW"
    REWRITE = "REWRITE"
    HOLD_FOR_REVIEW = "HOLD_FOR_REVIEW"
    SUPPRESS_FOR_GUIDANCE = "SUPPRESS_FOR_GUIDANCE"


class ReviewDecision(StrEnum):
    """Explicit decisions available to the synthetic review workflow."""

    APPROVE = "APPROVE"
    REPLACE_WITH_SAFE_TEMPLATE = "REPLACE_WITH_SAFE_TEMPLATE"
    HANDOFF = "HANDOFF"
    REJECT = "REJECT"


class SessionState(StrEnum):
    """States in the server-side synthetic role-play session lifecycle."""

    CREATED = "CREATED"
    ACTIVE = "ACTIVE"
    DRAFTING = "DRAFTING"
    CHECKING_DRAFT = "CHECKING_DRAFT"
    AWAITING_HUMAN_REVIEW = "AWAITING_HUMAN_REVIEW"
    RESPONSE_RELEASED = "RESPONSE_RELEASED"
    CLOSED = "CLOSED"
    FAILED_CLOSED = "FAILED_CLOSED"


class PluginKind(StrEnum):
    """Allowlisted extension points in the planned runtime."""

    MODEL_PROVIDER = "model_provider"
    INPUT_SAFETY_DETECTOR = "input_safety_detector"
    OUTPUT_GUARD = "output_guard"
    SUPPORT_MODULE = "support_module"
    TRAJECTORY_EVALUATOR = "trajectory_evaluator"
    REPORTER = "reporter"
    RESOURCE_CATALOG = "resource_catalog"
    AUTH_ADAPTER = "auth_adapter"
    INTEGRATION_ADAPTER = "integration_adapter"


class PluginFailureMode(StrEnum):
    """Whether plugin failure stops release or is isolated."""

    CRITICAL_FAIL_CLOSED = "critical_fail_closed"
    OPTIONAL_ISOLATED = "optional_isolated"


class SessionConfig(RuntimeContractModel):
    """Frozen configuration selected when a synthetic session is created."""

    contract_version: ContractVersion
    scenario_id: NonBlankStr
    locale: NonBlankStr
    plugin_profile_id: NonBlankStr
    max_draft_rewrite_attempts: Literal[2] = MAX_DRAFT_REWRITE_ATTEMPTS


class PluginManifestV1(RuntimeContractModel):
    """Static manifest discovered from an allowlisted Python entry point."""

    plugin_api_version: ContractVersion
    plugin_id: NonBlankStr
    plugin_version: NonBlankStr
    kind: PluginKind
    capabilities: NonEmptyStrings
    configuration_schema_id: NonBlankStr
    dependency_plugin_ids: tuple[NonBlankStr, ...]
    failure_mode: PluginFailureMode
    default_enabled: bool

    @model_validator(mode="after")
    def validate_failure_and_dependencies(self) -> Self:
        if len(set(self.capabilities)) != len(self.capabilities):
            raise ValueError("capabilities must be unique")
        if len(set(self.dependency_plugin_ids)) != len(self.dependency_plugin_ids):
            raise ValueError("dependency_plugin_ids must be unique")
        if self.plugin_id in self.dependency_plugin_ids:
            raise ValueError("dependency_plugin_ids must not contain plugin_id")
        critical_kinds = {
            PluginKind.MODEL_PROVIDER,
            PluginKind.INPUT_SAFETY_DETECTOR,
            PluginKind.OUTPUT_GUARD,
            PluginKind.RESOURCE_CATALOG,
        }
        if (
            self.kind in critical_kinds
            and self.failure_mode is not PluginFailureMode.CRITICAL_FAIL_CLOSED
        ):
            raise ValueError(f"{self.kind.value} plugins must fail_closed")
        return self


class DraftGateResult(RuntimeContractModel):
    """Evidence-linked decision over one quarantined model draft."""

    contract_version: ContractVersion
    draft_id: NonBlankStr
    decision: DraftDecision
    disposition: SafetyDisposition
    rewrite_count: Annotated[int, Field(ge=0, le=MAX_DRAFT_REWRITE_ATTEMPTS)]
    finding_ids: tuple[NonBlankStr, ...]

    @model_validator(mode="after")
    def validate_release_and_rewrite_constraints(self) -> Self:
        if (
            self.decision is DraftDecision.ALLOW
            and self.disposition is not SafetyDisposition.SUPPORT_ALLOWED
        ):
            raise ValueError("ALLOW requires SUPPORT_ALLOWED")
        if self.decision is DraftDecision.REWRITE:
            if not self.finding_ids:
                raise ValueError("REWRITE requires non-empty finding_ids")
            if self.rewrite_count >= MAX_DRAFT_REWRITE_ATTEMPTS:
                raise ValueError("REWRITE is forbidden at the rewrite limit")
            if self.disposition is not SafetyDisposition.CLARIFICATION_REQUIRED:
                raise ValueError("REWRITE requires CLARIFICATION_REQUIRED")
        if (
            self.decision is DraftDecision.SUPPRESS_FOR_GUIDANCE
            and self.disposition is not SafetyDisposition.EMERGENCY_GUIDANCE_REQUIRED
        ):
            raise ValueError(
                "SUPPRESS_FOR_GUIDANCE requires EMERGENCY_GUIDANCE_REQUIRED"
            )
        return self


class ModelRequest(RuntimeContractModel):
    """Provider-neutral request containing only validated synthetic context."""

    contract_version: ContractVersion
    request_id: NonBlankStr
    session_id: NonBlankStr
    input_turn: Turn
    context_turns: tuple[Turn, ...]
    locale: NonBlankStr
    prompt_template_id: NonBlankStr
    prompt_template_hash: Sha256Digest

    @model_validator(mode="after")
    def validate_turn_context(self) -> Self:
        if self.input_turn.role != "user":
            raise ValueError("input_turn must have the user role")
        context_ids = tuple(turn.turn_id for turn in self.context_turns)
        if len(set(context_ids)) != len(context_ids):
            raise ValueError("context_turns must have unique turn_id values")
        if self.input_turn.turn_id in context_ids:
            raise ValueError("input_turn must not be duplicated in context_turns")
        context_sequences = tuple(turn.sequence for turn in self.context_turns)
        if any(
            current <= previous
            for previous, current in zip(
                context_sequences,
                context_sequences[1:],
            )
        ):
            raise ValueError("context_turns sequence must be strictly increasing")
        if context_sequences and context_sequences[-1] >= self.input_turn.sequence:
            raise ValueError("context_turns must precede input_turn")
        return self


class ModelDraft(RuntimeContractModel):
    """A quarantined provider response that has not been released."""

    contract_version: ContractVersion
    request_id: NonBlankStr
    draft_id: NonBlankStr
    text: NonBlankStr
    provider_id: NonBlankStr
    model_name: NonBlankStr


class PluginVersionRef(RuntimeContractModel):
    """One exact plugin identity recorded in provenance."""

    plugin_id: NonBlankStr
    plugin_version: NonBlankStr


class ArtifactProvenance(RuntimeContractModel):
    """Replay-relevant component identity without hidden model reasoning."""

    contract_version: ContractVersion
    session_id: NonBlankStr
    scenario_id: NonBlankStr
    provider_id: NonBlankStr
    model_name: NonBlankStr
    prompt_template_id: NonBlankStr
    prompt_template_hash: Sha256Digest
    plugin_versions: tuple[PluginVersionRef, ...]
    resource_registry_version: NonBlankStr

    @model_validator(mode="after")
    def validate_unique_plugin_versions(self) -> Self:
        plugin_ids = tuple(item.plugin_id for item in self.plugin_versions)
        if len(set(plugin_ids)) != len(plugin_ids):
            raise ValueError("plugin_versions must contain unique plugin_id values")
        return self
