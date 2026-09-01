import asyncio
from dataclasses import dataclass

import pytest
from pydantic import ValidationError

from careloop.agent_runtime import (
    ModelDraft,
    ModelRequest,
    ModelRuntimeFailureCode,
    ModelRuntimeResult,
    PluginFailureMode,
    PluginKind,
    PluginManifestV1,
    ProviderNeutralModelRuntime,
    SessionEvent,
    SessionState,
)
from careloop.domain import Turn


def _request() -> ModelRequest:
    return ModelRequest(
        contract_version="v1",
        request_id="request-001",
        session_id="session-001",
        input_turn=Turn(
            turn_id="turn-001",
            sequence=0,
            role="user",
            text="Synthetic role-play input only.",
        ),
        context_turns=(),
        locale="en",
        prompt_template_id="support-shell.v1",
        prompt_template_hash="sha256:" + "a" * 64,
    )


def _provider_manifest() -> PluginManifestV1:
    return PluginManifestV1(
        plugin_api_version="v1",
        plugin_id="provider-deterministic-test",
        plugin_version="1.0.0",
        kind=PluginKind.MODEL_PROVIDER,
        capabilities=("synthetic-text-generation",),
        configuration_schema_id="provider-test.config.v1",
        dependency_plugin_ids=(),
        failure_mode=PluginFailureMode.CRITICAL_FAIL_CLOSED,
        default_enabled=False,
    )


def _draft(
    *,
    request_id: str = "request-001",
    provider_id: str = "provider-deterministic-test",
    model_name: str = "deterministic-model-v1",
) -> ModelDraft:
    return ModelDraft(
        contract_version="v1",
        request_id=request_id,
        draft_id="draft-001",
        text="Quarantined synthetic draft.",
        provider_id=provider_id,
        model_name=model_name,
    )


@dataclass
class DeterministicModelAdapter:
    output: object
    calls: int = 0

    async def generate(self, request: ModelRequest) -> ModelDraft:
        self.calls += 1
        if isinstance(self.output, BaseException):
            raise self.output
        return self.output  # type: ignore[return-value]


def _run(adapter: DeterministicModelAdapter):
    runtime = ProviderNeutralModelRuntime(
        model_port=adapter,
        provider_manifest=_provider_manifest(),
        model_name="deterministic-model-v1",
    )
    return asyncio.run(
        runtime.generate(
            _request(),
            event_id="event-001",
            event_sequence=2,
        )
    )


def test_model_runtime_returns_only_a_quarantined_correlated_draft() -> None:
    adapter = DeterministicModelAdapter(_draft())

    result = _run(adapter)

    assert adapter.calls == 1
    assert result.quarantined_draft == _draft()
    assert result.failure_code is None
    assert result.event.event is SessionEvent.DRAFT_GENERATED
    assert result.event.state_before is SessionState.DRAFTING
    assert result.event.state_after is SessionState.CHECKING_DRAFT
    assert result.event.evidence_ids == ("draft-001",)
    assert "visible_output" not in type(result).model_fields
    assert "released_turn" not in type(result).model_fields


@pytest.mark.parametrize(
    ("output", "expected_code"),
    [
        (TimeoutError("provider secret must not escape"), "provider_exception"),
        (object(), "invalid_draft"),
        (
            ModelDraft.model_construct(
                contract_version="v1",
                request_id="request-001",
                draft_id="draft-constructed",
                text="Quarantined synthetic draft.",
                provider_id=" ",
                model_name="deterministic-model-v1",
            ),
            "invalid_draft",
        ),
        (_draft(request_id="request-other"), "request_mismatch"),
        (_draft(provider_id="provider-other"), "provider_mismatch"),
        (_draft(model_name="model-other"), "model_mismatch"),
    ],
)
def test_provider_failures_and_malformed_or_mismatched_drafts_fail_closed(
    output: object,
    expected_code: str,
) -> None:
    result = _run(DeterministicModelAdapter(output))

    assert result.quarantined_draft is None
    assert result.failure_code is ModelRuntimeFailureCode(expected_code)
    assert result.event.event is SessionEvent.RUNTIME_FAILURE
    assert result.event.state_after is SessionState.FAILED_CLOSED
    assert result.event.evidence_ids == (f"model_runtime:{expected_code}",)
    assert "provider secret" not in result.model_dump_json()


def test_identical_explicit_inputs_and_adapter_output_are_deterministic() -> None:
    first = _run(DeterministicModelAdapter(_draft()))
    second = _run(DeterministicModelAdapter(_draft()))

    assert first.model_dump_json() == second.model_dump_json()


def test_model_runtime_result_rejects_inconsistent_evidence_and_unknown_fields() -> (
    None
):
    result = _run(DeterministicModelAdapter(_draft()))
    payload = result.model_dump(mode="json")
    payload["event"]["evidence_ids"] = ["draft-other"]

    with pytest.raises(ValidationError, match="evidence_ids"):
        ModelRuntimeResult.model_validate(payload)
    with pytest.raises(ValidationError, match="unexpected"):
        ModelRuntimeResult.model_validate(
            {**result.model_dump(mode="json"), "unexpected": True}
        )


def test_model_runtime_result_has_no_clinical_or_release_fields() -> None:
    forbidden = {
        "risk_score",
        "risk_level",
        "suicide_probability",
        "diagnosis",
        "clinical_disposition",
        "chain_of_thought",
        "visible_output",
        "released_turn",
    }

    assert forbidden.isdisjoint(ModelRuntimeResult.model_fields)


def test_model_runtime_requires_a_fail_closed_model_provider_manifest() -> None:
    manifest = _provider_manifest().model_copy(update={"kind": PluginKind.REPORTER})

    with pytest.raises(ValueError, match="model_provider"):
        ProviderNeutralModelRuntime(
            model_port=DeterministicModelAdapter(_draft()),
            provider_manifest=manifest,
            model_name="deterministic-model-v1",
        )
