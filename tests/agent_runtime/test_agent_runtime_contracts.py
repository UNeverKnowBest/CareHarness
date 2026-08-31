from typing import get_type_hints

import pytest
from pydantic import ValidationError

from careloop.agent_runtime import (
    MAX_DRAFT_REWRITE_ATTEMPTS,
    ArtifactProvenance,
    DraftDecision,
    DraftGateResult,
    ModelDraft,
    ModelPort,
    ModelRequest,
    PluginFailureMode,
    PluginKind,
    PluginManifestV1,
    PluginVersionRef,
    ReviewDecision,
    RuntimeEvent,
    SafetyDisposition,
    SessionConfig,
    SessionState,
)
from careloop.domain import Turn


def test_runtime_enums_freeze_non_clinical_control_vocabulary() -> None:
    assert {item.value for item in SafetyDisposition} == {
        "SUPPORT_ALLOWED",
        "CLARIFICATION_REQUIRED",
        "HUMAN_REVIEW_REQUIRED",
        "EMERGENCY_GUIDANCE_REQUIRED",
        "SYSTEM_FAILURE",
    }
    assert {item.value for item in DraftDecision} == {
        "ALLOW",
        "REWRITE",
        "HOLD_FOR_REVIEW",
        "SUPPRESS_FOR_GUIDANCE",
    }
    assert {item.value for item in ReviewDecision} == {
        "APPROVE",
        "REPLACE_WITH_SAFE_TEMPLATE",
        "HANDOFF",
        "REJECT",
    }
    assert {item.value for item in SessionState} == {
        "CREATED",
        "ACTIVE",
        "DRAFTING",
        "CHECKING_DRAFT",
        "AWAITING_HUMAN_REVIEW",
        "RESPONSE_RELEASED",
        "CLOSED",
        "FAILED_CLOSED",
    }


def test_session_config_fixes_two_rewrites_and_rejects_unknown_fields() -> None:
    config = SessionConfig(
        contract_version="v1",
        scenario_id="scenario-synthetic-001",
        locale="zh-CN",
        plugin_profile_id="profile-research-default",
    )

    assert config.max_draft_rewrite_attempts == MAX_DRAFT_REWRITE_ATTEMPTS == 2
    assert set(SessionConfig.model_fields) == {
        "contract_version",
        "scenario_id",
        "locale",
        "plugin_profile_id",
        "max_draft_rewrite_attempts",
    }

    with pytest.raises(ValidationError, match="max_draft_rewrite_attempts"):
        SessionConfig(
            contract_version="v1",
            scenario_id="scenario-synthetic-001",
            locale="zh-CN",
            plugin_profile_id="profile-research-default",
            max_draft_rewrite_attempts=3,
        )
    with pytest.raises(ValidationError, match="unexpected"):
        SessionConfig(
            contract_version="v1",
            scenario_id="scenario-synthetic-001",
            locale="zh-CN",
            plugin_profile_id="profile-research-default",
            unexpected=True,
        )


@pytest.mark.parametrize(
    "kind",
    [
        PluginKind.MODEL_PROVIDER,
        PluginKind.INPUT_SAFETY_DETECTOR,
        PluginKind.OUTPUT_GUARD,
        PluginKind.RESOURCE_CATALOG,
    ],
)
def test_safety_critical_plugins_must_fail_closed(kind: PluginKind) -> None:
    with pytest.raises(ValidationError, match="fail_closed"):
        PluginManifestV1(
            plugin_api_version="v1",
            plugin_id=f"plugin-{kind.value}",
            plugin_version="1.0.0",
            kind=kind,
            capabilities=("synthetic-demo",),
            configuration_schema_id="config.synthetic.v1",
            dependency_plugin_ids=(),
            failure_mode=PluginFailureMode.OPTIONAL_ISOLATED,
            default_enabled=False,
        )


def test_plugin_manifest_is_strict_and_dependency_ids_are_unique() -> None:
    manifest = PluginManifestV1(
        plugin_api_version="v1",
        plugin_id="plugin-output-guard",
        plugin_version="1.0.0",
        kind=PluginKind.OUTPUT_GUARD,
        capabilities=("structured-findings",),
        configuration_schema_id="output-guard-config.v1",
        dependency_plugin_ids=("plugin-policy-registry",),
        failure_mode=PluginFailureMode.CRITICAL_FAIL_CLOSED,
        default_enabled=True,
    )

    assert manifest.plugin_api_version == "v1"
    with pytest.raises(ValidationError, match="dependency_plugin_ids"):
        PluginManifestV1.model_validate(
            {
                **manifest.model_dump(),
                "dependency_plugin_ids": (
                    "plugin-policy-registry",
                    "plugin-policy-registry",
                ),
            }
        )


def test_plugin_capabilities_must_be_unique() -> None:
    with pytest.raises(ValidationError, match="capabilities"):
        PluginManifestV1(
            plugin_api_version="v1",
            plugin_id="plugin-reporter",
            plugin_version="1.0.0",
            kind=PluginKind.REPORTER,
            capabilities=("participant-report", "participant-report"),
            configuration_schema_id="reporter-config.v1",
            dependency_plugin_ids=(),
            failure_mode=PluginFailureMode.OPTIONAL_ISOLATED,
            default_enabled=False,
        )


def test_draft_gate_never_allows_non_support_disposition() -> None:
    allowed = DraftGateResult(
        contract_version="v1",
        draft_id="draft-001",
        decision=DraftDecision.ALLOW,
        disposition=SafetyDisposition.SUPPORT_ALLOWED,
        rewrite_count=0,
        finding_ids=(),
    )
    assert allowed.decision is DraftDecision.ALLOW

    with pytest.raises(ValidationError, match="SUPPORT_ALLOWED"):
        DraftGateResult(
            contract_version="v1",
            draft_id="draft-002",
            decision=DraftDecision.ALLOW,
            disposition=SafetyDisposition.HUMAN_REVIEW_REQUIRED,
            rewrite_count=0,
            finding_ids=("finding-001",),
        )


def test_rewrite_is_bounded_and_requires_evidence() -> None:
    with pytest.raises(ValidationError, match="finding_ids"):
        DraftGateResult(
            contract_version="v1",
            draft_id="draft-001",
            decision=DraftDecision.REWRITE,
            disposition=SafetyDisposition.CLARIFICATION_REQUIRED,
            rewrite_count=0,
            finding_ids=(),
        )
    with pytest.raises(ValidationError, match="rewrite limit"):
        DraftGateResult(
            contract_version="v1",
            draft_id="draft-002",
            decision=DraftDecision.REWRITE,
            disposition=SafetyDisposition.HUMAN_REVIEW_REQUIRED,
            rewrite_count=2,
            finding_ids=("finding-001",),
        )
    with pytest.raises(ValidationError, match="CLARIFICATION_REQUIRED"):
        DraftGateResult(
            contract_version="v1",
            draft_id="draft-003",
            decision=DraftDecision.REWRITE,
            disposition=SafetyDisposition.SUPPORT_ALLOWED,
            rewrite_count=0,
            finding_ids=("finding-001",),
        )


def test_provider_neutral_model_contract_has_no_sdk_types() -> None:
    request = ModelRequest(
        contract_version="v1",
        request_id="request-001",
        session_id="session-001",
        input_turn=Turn(
            turn_id="turn-001",
            sequence=0,
            role="user",
            text="Synthetic role-play input.",
        ),
        context_turns=(),
        locale="en",
        prompt_template_id="support-shell.v1",
        prompt_template_hash="sha256:" + "a" * 64,
    )
    draft = ModelDraft(
        contract_version="v1",
        request_id=request.request_id,
        draft_id="draft-001",
        text="Synthetic draft.",
        provider_id="provider-cloud-test",
        model_name="model-test",
    )

    assert draft.request_id == request.request_id
    type_hints = get_type_hints(ModelPort.generate)
    assert type_hints["request"] is ModelRequest
    assert type_hints["return"] is ModelDraft
    with pytest.raises(ValidationError, match="prompt_template_hash"):
        ModelRequest.model_validate(
            {
                **request.model_dump(),
                "prompt_template_hash": "not-a-hash",
            }
        )


def test_model_context_must_precede_input_in_sequence_order() -> None:
    input_turn = Turn(
        turn_id="turn-input",
        sequence=2,
        role="user",
        text="Synthetic role-play input.",
    )
    out_of_order = (
        Turn(turn_id="turn-002", sequence=1, role="assistant", text="Second."),
        Turn(turn_id="turn-001", sequence=0, role="user", text="First."),
    )

    with pytest.raises(ValidationError, match="strictly increasing"):
        ModelRequest(
            contract_version="v1",
            request_id="request-order",
            session_id="session-001",
            input_turn=input_turn,
            context_turns=out_of_order,
            locale="en",
            prompt_template_id="support-shell.v1",
            prompt_template_hash="sha256:" + "c" * 64,
        )

    with pytest.raises(ValidationError, match="precede input_turn"):
        ModelRequest(
            contract_version="v1",
            request_id="request-future",
            session_id="session-001",
            input_turn=input_turn,
            context_turns=(
                Turn(
                    turn_id="turn-future",
                    sequence=3,
                    role="assistant",
                    text="Future.",
                ),
            ),
            locale="en",
            prompt_template_id="support-shell.v1",
            prompt_template_hash="sha256:" + "d" * 64,
        )


def test_provenance_rejects_duplicate_plugins_and_forbidden_clinical_fields() -> None:
    plugin = PluginVersionRef(
        plugin_id="plugin-output-guard",
        plugin_version="1.0.0",
    )
    with pytest.raises(ValidationError, match="plugin_versions"):
        ArtifactProvenance(
            contract_version="v1",
            session_id="session-001",
            scenario_id="scenario-synthetic-001",
            provider_id="provider-cloud-test",
            model_name="model-test",
            prompt_template_id="support-shell.v1",
            prompt_template_hash="sha256:" + "b" * 64,
            plugin_versions=(plugin, plugin),
            resource_registry_version="v1",
        )

    forbidden = {
        "risk_score",
        "risk_level",
        "suicide_probability",
        "diagnosis",
        "clinical_disposition",
        "chain_of_thought",
    }
    public_models = (
        SessionConfig,
        PluginManifestV1,
        DraftGateResult,
        ModelRequest,
        ModelDraft,
        PluginVersionRef,
        ArtifactProvenance,
        RuntimeEvent,
    )
    for model in public_models:
        assert forbidden.isdisjoint(model.model_fields)
