import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from careloop.agent_runtime import (
    DraftDecision,
    DraftGateResult,
    ModelDraft,
    ModelRequest,
    PluginFailureMode,
    PluginKind,
    PluginManifestV1,
    ProviderNeutralModelRuntime,
    RuntimeEvent,
    SafetyDisposition,
    SessionConfig,
    SessionEvent,
    SessionState,
)
from careloop.application.synthetic_turn import (
    EthicalDraftGate,
    IdempotencyConflict,
    ParticipantTurnView,
    ResearchReviewTurnView,
    RunSyntheticTurn,
    SessionNotRunnable,
    SyntheticTurnCommand,
    SyntheticTurnFailureCode,
    SyntheticTurnStatus,
)
from careloop.domain import Turn
from careloop.runtime_storage import InMemoryRuntimeEventLedger
from careloop.safety import (
    CrisisRouter,
    EthicalOutputPolicy,
    SyntheticSafetyRuntime,
    SyntheticSafetySignalDetector,
    load_crisis_policy,
    load_ethical_policy,
    load_resource_registry,
)

ROOT = Path(__file__).parents[2]
POLICY_ROOT = ROOT / "policies"
AS_OF = date(2026, 8, 29)


def _config(profile: str = "profile-synthetic-default") -> SessionConfig:
    return SessionConfig(
        contract_version="v1",
        scenario_id="scenario-synthetic-001",
        locale="en",
        plugin_profile_id=profile,
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


def _command(
    *,
    request_id: str = "command-001",
    text: str = "[SYNTHETIC] No frozen safety signal.",
) -> SyntheticTurnCommand:
    return SyntheticTurnCommand(
        contract_version="v1",
        request_id=request_id,
        input_turn=Turn(
            turn_id=f"{request_id}:user",
            sequence=0,
            role="user",
            text=text,
        ),
        context_turns=(),
        jurisdiction="ZZ-TEST",
        as_of=AS_OF,
        prompt_template_id="support-shell.v1",
        prompt_template_hash="sha256:" + "a" * 64,
    )


@dataclass
class ScriptedModelAdapter:
    outputs: tuple[str | BaseException, ...]
    calls: list[str] = field(default_factory=list)

    async def generate(self, request: ModelRequest) -> ModelDraft:
        index = len(self.calls)
        self.calls.append(request.request_id)
        output = self.outputs[index]
        if isinstance(output, BaseException):
            raise output
        return ModelDraft(
            contract_version="v1",
            request_id=request.request_id,
            draft_id=f"draft-{index}",
            text=output,
            provider_id="provider-deterministic-test",
            model_name="deterministic-model-v1",
        )


@dataclass
class ScriptedDraftGate:
    decisions: tuple[DraftDecision, ...]
    calls: list[tuple[str, int]] = field(default_factory=list)

    def check(
        self,
        draft: ModelDraft,
        *,
        input_turn: Turn,
        rewrite_count: int,
    ) -> DraftGateResult:
        del input_turn
        self.calls.append((draft.draft_id, rewrite_count))
        decision = self.decisions[len(self.calls) - 1]
        if decision is DraftDecision.ALLOW:
            disposition = SafetyDisposition.SUPPORT_ALLOWED
            finding_ids: tuple[str, ...] = ()
        elif decision is DraftDecision.REWRITE:
            disposition = SafetyDisposition.CLARIFICATION_REQUIRED
            finding_ids = (f"finding-{rewrite_count}",)
        elif decision is DraftDecision.SUPPRESS_FOR_GUIDANCE:
            disposition = SafetyDisposition.EMERGENCY_GUIDANCE_REQUIRED
            finding_ids = (f"finding-{rewrite_count}",)
        else:
            disposition = SafetyDisposition.HUMAN_REVIEW_REQUIRED
            finding_ids = (f"finding-{rewrite_count}",)
        return DraftGateResult(
            contract_version="v1",
            draft_id=draft.draft_id,
            decision=decision,
            disposition=disposition,
            rewrite_count=rewrite_count,
            finding_ids=finding_ids,
        )


class RaisingDraftGate:
    def check(self, *_args: object, **_kwargs: object) -> DraftGateResult:
        raise RuntimeError("gate secret must not escape")


class RaisingDetector:
    def detect(self, _turn: Turn) -> object:
        raise RuntimeError("detector secret must not escape")


class RaisingRouter:
    def route(self, *_args: object, **_kwargs: object) -> object:
        raise RuntimeError("router secret must not escape")


class SafetySpy:
    def __init__(self, delegate: SyntheticSafetyRuntime, calls: list[str]) -> None:
        self._delegate = delegate
        self._calls = calls

    def route_input(self, *args: object, **kwargs: object) -> object:
        self._calls.append("safety")
        return self._delegate.route_input(*args, **kwargs)


def _safety_runtime(
    *,
    detector: object | None = None,
    router: object | None = None,
    resource_loader: Callable[[], object] | None = None,
) -> tuple[SyntheticSafetyRuntime, EthicalOutputPolicy]:
    crisis = load_crisis_policy(POLICY_ROOT / "crisis.v1.json")
    ethical = load_ethical_policy(POLICY_ROOT / "ethical.v1.json")
    resources = load_resource_registry(POLICY_ROOT / "resources.v1.json")
    output_policy = EthicalOutputPolicy(ethical)
    return (
        SyntheticSafetyRuntime(
            crisis,
            detector=detector or SyntheticSafetySignalDetector(crisis),
            router=router
            or CrisisRouter(crisis, resource_loader or (lambda: resources)),
            output_policy=output_policy,
        ),
        output_policy,
    )


def _runner(
    *,
    model: ScriptedModelAdapter,
    gate: object,
    safety_runtime: object | None = None,
    ledger: object | None = None,
) -> RunSyntheticTurn:
    actual_safety = safety_runtime or _safety_runtime()[0]
    return RunSyntheticTurn(
        session_id="session-001",
        session_config=_config(),
        safety_runtime=actual_safety,
        model_runtime=ProviderNeutralModelRuntime(
            model_port=model,
            provider_manifest=_provider_manifest(),
            model_name="deterministic-model-v1",
        ),
        draft_gate=gate,
        ledger=ledger or InMemoryRuntimeEventLedger(),
    )


def _execute(runner: RunSyntheticTurn, command: SyntheticTurnCommand):
    return asyncio.run(runner.execute(command))


def test_safe_turn_routes_input_then_checks_draft_before_atomic_release() -> None:
    calls: list[str] = []
    safety, _ = _safety_runtime()
    safety_spy = SafetySpy(safety, calls)

    class OrderedModel(ScriptedModelAdapter):
        async def generate(self, request: ModelRequest) -> ModelDraft:
            calls.append("model")
            return await super().generate(request)

    class OrderedGate(ScriptedDraftGate):
        def check(self, *args: object, **kwargs: object) -> DraftGateResult:
            calls.append("gate")
            return super().check(*args, **kwargs)

    model = OrderedModel(("[SYNTHETIC] Allowed draft.",))
    gate = OrderedGate((DraftDecision.ALLOW,))
    result = _execute(
        _runner(model=model, gate=gate, safety_runtime=safety_spy),
        _command(),
    )

    assert calls == ["safety", "model", "gate"]
    assert result.participant.status is SyntheticTurnStatus.RELEASED
    assert result.participant.state is SessionState.RESPONSE_RELEASED
    assert result.participant.released_turn is not None
    assert result.participant.released_turn.text == "[SYNTHETIC] Allowed draft."
    assert tuple(event.event for event in result.runtime_events) == (
        SessionEvent.START_SESSION,
        SessionEvent.SUBMIT_TURN,
        SessionEvent.DRAFT_GENERATED,
        SessionEvent.DRAFT_APPROVED,
    )
    assert len(result.quarantined_drafts) == 1


def test_crisis_override_suppresses_model_gate_and_ordinary_release() -> None:
    model = ScriptedModelAdapter(("must not be called",))
    gate = ScriptedDraftGate((DraftDecision.ALLOW,))
    result = _execute(
        _runner(model=model, gate=gate),
        _command(
            text=("[SYNTHETIC SAFETY SIGNAL: CURRENT PLAN] Frozen fictional evidence.")
        ),
    )

    assert result.participant.status is SyntheticTurnStatus.OVERRIDE_SUPPRESSED
    assert result.participant.released_turn is None
    assert result.participant.safety_event is not None
    assert result.participant.safety_event.normal_flow_suppressed is True
    assert model.calls == []
    assert gate.calls == []
    assert tuple(event.event for event in result.runtime_events) == (
        SessionEvent.START_SESSION,
    )


@pytest.mark.parametrize("failure", ["input", "router", "resource"])
def test_input_router_and_resource_failures_append_runtime_failure(
    failure: str,
) -> None:
    if failure == "input":
        safety = _safety_runtime(detector=RaisingDetector())[0]
        text = "[SYNTHETIC] No frozen signal."
    elif failure == "router":
        safety = _safety_runtime(router=RaisingRouter())[0]
        text = "[SYNTHETIC SAFETY SIGNAL: CURRENT PLAN] Frozen evidence."
    else:

        def raising_loader() -> object:
            raise RuntimeError("resource secret must not escape")

        safety = _safety_runtime(resource_loader=raising_loader)[0]
        text = "[SYNTHETIC SAFETY SIGNAL: CURRENT PLAN] Frozen evidence."
    model = ScriptedModelAdapter(("must not be called",))
    result = _execute(
        _runner(
            model=model,
            gate=ScriptedDraftGate((DraftDecision.ALLOW,)),
            safety_runtime=safety,
        ),
        _command(text=text),
    )

    assert result.failure_code is SyntheticTurnFailureCode.INPUT_SAFETY_FAILURE
    assert result.participant.status is SyntheticTurnStatus.FAILED_CLOSED
    assert result.participant.released_turn is None
    assert result.runtime_events[-1].event is SessionEvent.RUNTIME_FAILURE
    assert result.runtime_events[-1].state_after is SessionState.FAILED_CLOSED
    assert model.calls == []
    assert "secret" not in result.model_dump_json()


def test_model_and_gate_failures_fail_closed_without_fallback() -> None:
    model_failure = _execute(
        _runner(
            model=ScriptedModelAdapter((TimeoutError("provider secret"),)),
            gate=ScriptedDraftGate((DraftDecision.ALLOW,)),
        ),
        _command(request_id="command-model-failure"),
    )
    assert model_failure.failure_code is SyntheticTurnFailureCode.MODEL_RUNTIME_FAILURE
    assert model_failure.participant.released_turn is None
    assert model_failure.runtime_events[-1].event is SessionEvent.RUNTIME_FAILURE

    gate_failure = _execute(
        _runner(
            model=ScriptedModelAdapter(("[SYNTHETIC] Draft.",)),
            gate=RaisingDraftGate(),
        ),
        _command(request_id="command-gate-failure"),
    )
    assert gate_failure.failure_code is SyntheticTurnFailureCode.DRAFT_GATE_FAILURE
    assert gate_failure.participant.released_turn is None
    assert gate_failure.runtime_events[-1].state_before is SessionState.CHECKING_DRAFT
    assert "secret" not in gate_failure.model_dump_json()


def test_two_rewrites_then_third_failed_draft_enters_review_hold() -> None:
    model = ScriptedModelAdapter(("draft zero", "draft one", "draft two"))
    gate = ScriptedDraftGate(
        (
            DraftDecision.REWRITE,
            DraftDecision.REWRITE,
            DraftDecision.HOLD_FOR_REVIEW,
        )
    )
    runner = _runner(model=model, gate=gate)
    result = _execute(runner, _command())

    assert len(model.calls) == 3
    assert [count for _, count in gate.calls] == [0, 1, 2]
    assert result.participant.status is SyntheticTurnStatus.AWAITING_HUMAN_REVIEW
    assert result.participant.state is SessionState.AWAITING_HUMAN_REVIEW
    assert result.participant.released_turn is None
    assert result.runtime_events[-1].event is SessionEvent.DRAFT_HELD_FOR_REVIEW

    with pytest.raises(SessionNotRunnable, match="AWAITING_HUMAN_REVIEW"):
        _execute(runner, _command(request_id="command-bypass"))
    assert len(model.calls) == 3


def test_existing_ethical_output_policy_rewrites_before_release() -> None:
    safety, output_policy = _safety_runtime()
    model = ScriptedModelAdapter(
        (
            "[SYNTHETIC] After one denial, you are safe.",
            "[SYNTHETIC] Revised neutral support response.",
        )
    )
    result = _execute(
        _runner(
            model=model,
            gate=EthicalDraftGate(output_policy),
            safety_runtime=safety,
        ),
        _command(),
    )

    assert tuple(item.decision for item in result.draft_gate_results) == (
        DraftDecision.REWRITE,
        DraftDecision.ALLOW,
    )
    assert result.participant.status is SyntheticTurnStatus.RELEASED
    assert result.participant.released_turn is not None
    assert result.participant.released_turn.text.endswith("support response.")


def test_exact_retry_is_idempotent_and_conflicting_retry_rejects() -> None:
    safety_calls: list[str] = []
    safety = SafetySpy(_safety_runtime()[0], safety_calls)
    ledger = InMemoryRuntimeEventLedger()
    model = ScriptedModelAdapter(("[SYNTHETIC] Allowed draft.",))
    gate = ScriptedDraftGate((DraftDecision.ALLOW,))
    runner = _runner(model=model, gate=gate, safety_runtime=safety, ledger=ledger)
    command = _command()

    first = _execute(runner, command)
    second = _execute(runner, command)

    assert first == second
    assert len(model.calls) == 1
    assert len(gate.calls) == 1
    assert safety_calls == ["safety"]
    assert len(ledger.events_for("session-001")) == 4
    with pytest.raises(IdempotencyConflict, match="request_id"):
        _execute(
            runner,
            command.model_copy(
                update={
                    "input_turn": command.input_turn.model_copy(
                        update={"text": "[SYNTHETIC] Changed retry."}
                    )
                }
            ),
        )


def test_idempotency_cache_uses_deep_command_and_result_snapshots() -> None:
    model = ScriptedModelAdapter(("[SYNTHETIC] Original release.",))
    gate = ScriptedDraftGate((DraftDecision.ALLOW,))
    runner = _runner(model=model, gate=gate)
    command = _command()
    first = _execute(runner, command)
    assert first.participant.released_turn is not None

    first.participant.released_turn.text = "tampered result"
    command.input_turn.text = "tampered command"
    retried = _execute(runner, _command())

    assert retried.participant.released_turn is not None
    assert retried.participant.released_turn.text == "[SYNTHETIC] Original release."
    assert len(model.calls) == 1


def test_constructed_invalid_command_rejects_before_any_ledger_append() -> None:
    ledger = InMemoryRuntimeEventLedger()
    runner = _runner(
        model=ScriptedModelAdapter(("must not be called",)),
        gate=ScriptedDraftGate((DraftDecision.ALLOW,)),
        ledger=ledger,
    )
    invalid = SyntheticTurnCommand.model_construct(
        **{
            **_command().model_dump(),
            "input_turn": Turn(
                turn_id="invalid-assistant",
                sequence=0,
                role="assistant",
                text="[SYNTHETIC] Invalid command role.",
            ),
        }
    )

    with pytest.raises(ValidationError, match="input_turn"):
        _execute(runner, invalid)

    assert ledger.events_for("session-001") == ()


class OneShotApprovalFailureLedger:
    def __init__(self) -> None:
        self.delegate = InMemoryRuntimeEventLedger()
        self.failed = False

    def bind_session(self, session_id: str, config: SessionConfig) -> None:
        self.delegate.bind_session(session_id, config)

    def append(self, event: RuntimeEvent) -> None:
        if event.event is SessionEvent.DRAFT_APPROVED and not self.failed:
            self.failed = True
            raise RuntimeError("ledger secret must not escape")
        self.delegate.append(event)

    def events_for(self, session_id: str) -> tuple[RuntimeEvent, ...]:
        return self.delegate.events_for(session_id)

    def state_for(self, session_id: str) -> SessionState:
        return self.delegate.state_for(session_id)

    def next_sequence(self, session_id: str) -> int:
        return self.delegate.next_sequence(session_id)


def test_approval_ledger_failure_prevents_release_and_records_failure() -> None:
    ledger = OneShotApprovalFailureLedger()
    result = _execute(
        _runner(
            model=ScriptedModelAdapter(("[SYNTHETIC] Allowed draft.",)),
            gate=ScriptedDraftGate((DraftDecision.ALLOW,)),
            ledger=ledger,
        ),
        _command(),
    )

    assert result.failure_code is SyntheticTurnFailureCode.LEDGER_FAILURE
    assert result.participant.released_turn is None
    assert ledger.state_for("session-001") is SessionState.FAILED_CLOSED
    assert ledger.events_for("session-001")[-1].event is SessionEvent.RUNTIME_FAILURE


def test_command_and_audience_models_are_strict_and_isolated() -> None:
    with pytest.raises(ValidationError, match="unexpected"):
        SyntheticTurnCommand.model_validate(
            {**_command().model_dump(mode="json"), "unexpected": True}
        )

    assert set(ParticipantTurnView.model_fields) == {
        "contract_version",
        "request_id",
        "session_id",
        "status",
        "state",
        "released_turn",
        "safety_event",
        "resources",
    }
    assert set(ResearchReviewTurnView.model_fields) == {
        "contract_version",
        "participant",
        "quarantined_drafts",
        "draft_gate_results",
        "runtime_events",
        "failure_code",
    }
    participant_forbidden = {
        "quarantined_drafts",
        "draft_gate_results",
        "runtime_events",
        "failure_code",
        "chain_of_thought",
        "risk_score",
        "diagnosis",
        "clinical_disposition",
    }
    assert participant_forbidden.isdisjoint(ParticipantTurnView.model_fields)


def test_override_projection_rejects_terminal_runtime_state() -> None:
    result = _execute(
        _runner(
            model=ScriptedModelAdapter(("must not be called",)),
            gate=ScriptedDraftGate((DraftDecision.ALLOW,)),
        ),
        _command(text="[SYNTHETIC SAFETY SIGNAL: CURRENT PLAN] Frozen evidence."),
    )
    payload = result.participant.model_dump(mode="json")
    payload["state"] = SessionState.FAILED_CLOSED.value

    with pytest.raises(ValidationError, match="override_suppressed"):
        ParticipantTurnView.model_validate(payload)
