from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest
from pydantic import ValidationError

from careloop.agent_runtime import (
    RuntimeEvent,
    SessionConfig,
    SessionEvent,
    SessionState,
)
from careloop.application import EvaluateTrajectory
from careloop.application.synthetic_close import (
    CloseSyntheticSession,
    ParticipantSessionCloseView,
    ResearchSessionCloseView,
    SessionCloseIdempotencyConflict,
    SessionCloseLedgerUnavailable,
    SessionCloseStateConflict,
    SyntheticSessionCloseCommand,
    SyntheticSessionCloseFailureCode,
    SyntheticSessionCloseStatus,
    SyntheticSessionSnapshot,
)
from careloop.domain import SafetyAction, SafetyEvent, Turn
from careloop.evaluation import TrajectoryEvaluationResult
from careloop.runtime_storage import InMemoryRuntimeEventLedger

ROOT = Path(__file__).parents[2]


def _config() -> SessionConfig:
    return SessionConfig(
        contract_version="v1",
        scenario_id="scenario-synthetic-close",
        locale="en",
        plugin_profile_id="profile-synthetic-close",
    )


def _event(
    *,
    event_id: str,
    sequence: int,
    event: SessionEvent,
    before: SessionState,
    after: SessionState,
    causation_id: str,
    evidence_ids: tuple[str, ...],
) -> RuntimeEvent:
    return RuntimeEvent(
        contract_version="v1",
        event_id=event_id,
        session_id="session-close-001",
        sequence=sequence,
        event=event,
        state_before=before,
        state_after=after,
        causation_id=causation_id,
        evidence_ids=evidence_ids,
    )


def _released_ledger() -> InMemoryRuntimeEventLedger:
    ledger = InMemoryRuntimeEventLedger()
    ledger.bind_session("session-close-001", _config())
    for event in (
        _event(
            event_id="event-start",
            sequence=0,
            event=SessionEvent.START_SESSION,
            before=SessionState.CREATED,
            after=SessionState.ACTIVE,
            causation_id="session-close-001:create",
            evidence_ids=("scenario-synthetic-close",),
        ),
        _event(
            event_id="event-submit",
            sequence=1,
            event=SessionEvent.SUBMIT_TURN,
            before=SessionState.ACTIVE,
            after=SessionState.DRAFTING,
            causation_id="turn-request-001",
            evidence_ids=("turn-user",),
        ),
        _event(
            event_id="event-draft",
            sequence=2,
            event=SessionEvent.DRAFT_GENERATED,
            before=SessionState.DRAFTING,
            after=SessionState.CHECKING_DRAFT,
            causation_id="model-request-001",
            evidence_ids=("draft-001",),
        ),
        _event(
            event_id="event-approved",
            sequence=3,
            event=SessionEvent.DRAFT_APPROVED,
            before=SessionState.CHECKING_DRAFT,
            after=SessionState.RESPONSE_RELEASED,
            causation_id="draft-001",
            evidence_ids=("draft-001",),
        ),
    ):
        ledger.append(event)
    return ledger


def _review_released_ledger() -> InMemoryRuntimeEventLedger:
    ledger = InMemoryRuntimeEventLedger()
    ledger.bind_session("session-close-001", _config())
    for event in (
        _event(
            event_id="review-event-start",
            sequence=0,
            event=SessionEvent.START_SESSION,
            before=SessionState.CREATED,
            after=SessionState.ACTIVE,
            causation_id="session-close-001:create",
            evidence_ids=("scenario-synthetic-close",),
        ),
        _event(
            event_id="review-event-submit",
            sequence=1,
            event=SessionEvent.SUBMIT_TURN,
            before=SessionState.ACTIVE,
            after=SessionState.DRAFTING,
            causation_id="turn-request-review",
            evidence_ids=("turn-user",),
        ),
        _event(
            event_id="review-event-draft",
            sequence=2,
            event=SessionEvent.DRAFT_GENERATED,
            before=SessionState.DRAFTING,
            after=SessionState.CHECKING_DRAFT,
            causation_id="model-request-review",
            evidence_ids=("draft-review",),
        ),
        _event(
            event_id="review-event-held",
            sequence=3,
            event=SessionEvent.DRAFT_HELD_FOR_REVIEW,
            before=SessionState.CHECKING_DRAFT,
            after=SessionState.AWAITING_HUMAN_REVIEW,
            causation_id="draft-review",
            evidence_ids=("draft-review", "finding-review"),
        ),
        _event(
            event_id="review-event-replaced",
            sequence=4,
            event=SessionEvent.REVIEW_REPLACED,
            before=SessionState.AWAITING_HUMAN_REVIEW,
            after=SessionState.RESPONSE_RELEASED,
            causation_id="review-request",
            evidence_ids=(
                "draft-review",
                "review-evidence",
                "turn-review-assistant",
            ),
        ),
    ):
        ledger.append(event)
    return ledger


def _snapshot(
    *,
    assistant_id: str = "turn-user:assistant",
    include_override: bool = False,
) -> SyntheticSessionSnapshot:
    turns = (
        Turn(
            turn_id="turn-user",
            sequence=0,
            role="user",
            text="[SYNTHETIC] Please offer ordinary support.",
        ),
        Turn(
            turn_id=assistant_id,
            sequence=1,
            role="assistant",
            text="[SYNTHETIC] What would feel useful to discuss?",
        ),
    )
    safety_events: tuple[SafetyEvent, ...] = ()
    if include_override:
        turns += (
            Turn(
                turn_id="turn-override-user",
                sequence=2,
                role="user",
                text=(
                    "[SYNTHETIC SAFETY SIGNAL: AMBIGUOUS CURRENT] "
                    "Frozen role-play evidence."
                ),
            ),
        )
        safety_events = (
            SafetyEvent(
                event_id="safety-override-001",
                triggering_turn_ids=("turn-override-user",),
                action=SafetyAction.PAUSE_AND_CLARIFY_NOW,
                requires_override=True,
                normal_flow_suppressed=True,
                source_ids=("source-guide-m4-safety",),
                resource_ids=(),
                crisis_policy_version="v1",
            ),
        )
    return SyntheticSessionSnapshot(
        contract_version="v1",
        session_id="session-close-001",
        trajectory_id="trajectory-session-close-001",
        turns=turns,
        process_markers=(),
        safety_events=safety_events,
    )


def _command(
    *,
    request_id: str = "close-request-001",
    session_id: str = "session-close-001",
) -> SyntheticSessionCloseCommand:
    return SyntheticSessionCloseCommand(
        contract_version="v1",
        request_id=request_id,
        session_id=session_id,
        trajectory_id="trajectory-session-close-001",
        evidence_ids=("synthetic-session-complete",),
    )


def _evaluator() -> EvaluateTrajectory:
    return EvaluateTrajectory.from_paths(
        benchmark_manifest_path=ROOT / "benchmarks" / "manifest.v1.json",
        process_policy_path=ROOT / "policies" / "process.v1.json",
        crisis_policy_path=ROOT / "policies" / "crisis.v1.json",
        resource_policy_path=ROOT / "policies" / "resources.v1.json",
        evaluation_policy_path=ROOT / "policies" / "evaluation.v1.json",
    )


def test_close_evaluates_in_memory_then_appends_before_report_release() -> None:
    ledger = _released_ledger()
    calls: list[str] = []

    class OrderedEvaluator:
        def evaluate_artifact(self, artifact: object) -> TrajectoryEvaluationResult:
            calls.append(ledger.state_for("session-close-001").value)
            return _evaluator().evaluate_artifact(artifact)  # type: ignore[arg-type]

    result = CloseSyntheticSession(
        ledger=ledger,
        snapshot=_snapshot(),
        evaluator=OrderedEvaluator(),
    ).execute(_command())

    assert calls == [SessionState.RESPONSE_RELEASED.value]
    assert result.participant.status is SyntheticSessionCloseStatus.EVALUATED
    assert result.participant.state is SessionState.CLOSED
    assert result.participant.final_answer is not None
    assert result.participant.final_answer.turn_id == "turn-user:assistant"
    assert result.evaluation is not None
    assert result.evaluation.trajectory == _snapshot().trajectory()
    assert result.evaluation.case_id == "trajectory-session-close-001"
    assert result.runtime_event.event is SessionEvent.CLOSE_SESSION
    assert result.runtime_event.evidence_ids[:2] == (
        result.evaluation.case_id,
        result.evaluation.canonical_hash,
    )
    assert ledger.events_for("session-close-001")[-1] == result.runtime_event


def test_override_turn_is_authorized_only_by_suppressed_safety_evidence() -> None:
    result = CloseSyntheticSession(
        ledger=_released_ledger(),
        snapshot=_snapshot(include_override=True),
        evaluator=_evaluator(),
    ).execute(_command())

    assert result.evaluation is not None
    assert result.evaluation.trajectory.turns[-1].turn_id == "turn-override-user"
    assert result.evaluation.trajectory.safety_events[0].normal_flow_suppressed is True


def test_reviewed_replacement_event_authorizes_the_released_assistant_turn() -> None:
    result = CloseSyntheticSession(
        ledger=_review_released_ledger(),
        snapshot=_snapshot(assistant_id="turn-review-assistant"),
        evaluator=_evaluator(),
    ).execute(_command())

    assert result.participant.status is SyntheticSessionCloseStatus.EVALUATED
    assert result.participant.final_answer is not None
    assert result.participant.final_answer.turn_id == "turn-review-assistant"


@pytest.mark.parametrize("mismatch", ["session", "trajectory", "turn"])
def test_mismatched_or_unevidenced_snapshot_rejects_before_evaluation_or_append(
    mismatch: str,
) -> None:
    ledger = _released_ledger()
    snapshot = _snapshot(
        assistant_id=(
            "unreleased-assistant" if mismatch == "turn" else "turn-user:assistant"
        )
    )
    command = _command(
        session_id="session-other" if mismatch == "session" else "session-close-001"
    )
    if mismatch == "trajectory":
        command = command.model_copy(update={"trajectory_id": "trajectory-other"})

    class MustNotEvaluate:
        def evaluate_artifact(self, _artifact: object) -> TrajectoryEvaluationResult:
            raise AssertionError("evaluator must not be called")

    before = ledger.events_for("session-close-001")
    with pytest.raises(SessionCloseStateConflict):
        CloseSyntheticSession(
            ledger=ledger,
            snapshot=snapshot,
            evaluator=MustNotEvaluate(),
        ).execute(command)
    assert ledger.events_for("session-close-001") == before


def test_evaluation_failure_records_category_only_failed_closed_result() -> None:
    class RaisingEvaluator:
        def evaluate_artifact(self, _artifact: object) -> TrajectoryEvaluationResult:
            raise RuntimeError("evaluation secret must not escape")

    result = CloseSyntheticSession(
        ledger=_released_ledger(),
        snapshot=_snapshot(),
        evaluator=RaisingEvaluator(),
    ).execute(_command())

    assert result.participant.status is SyntheticSessionCloseStatus.FAILED_CLOSED
    assert result.participant.state is SessionState.FAILED_CLOSED
    assert result.participant.final_answer is None
    assert result.evaluation is None
    assert result.failure_code is SyntheticSessionCloseFailureCode.EVALUATION_FAILURE
    assert result.runtime_event.event is SessionEvent.RUNTIME_FAILURE
    assert result.runtime_event.evidence_ids == (
        "synthetic_session_close:evaluation_failure",
    )
    assert "secret" not in result.model_dump_json()


def test_substituted_evaluation_identity_fails_closed() -> None:
    class SubstitutingEvaluator:
        def evaluate_artifact(self, artifact: object) -> TrajectoryEvaluationResult:
            result = _evaluator().evaluate_artifact(artifact)  # type: ignore[arg-type]
            return result.model_copy(update={"canonical_hash": "sha256:" + "f" * 64})

    result = CloseSyntheticSession(
        ledger=_released_ledger(),
        snapshot=_snapshot(),
        evaluator=SubstitutingEvaluator(),
    ).execute(_command())

    assert result.failure_code is SyntheticSessionCloseFailureCode.EVALUATION_FAILURE
    assert result.evaluation is None
    assert result.runtime_event.event is SessionEvent.RUNTIME_FAILURE


@dataclass
class FailingCloseLedger:
    delegate: InMemoryRuntimeEventLedger
    persistent: bool

    def bind_session(self, session_id: str, config: SessionConfig) -> None:
        self.delegate.bind_session(session_id, config)

    def append(self, event: RuntimeEvent) -> None:
        if event.event is SessionEvent.CLOSE_SESSION or (
            self.persistent and event.event is SessionEvent.RUNTIME_FAILURE
        ):
            raise RuntimeError("ledger secret must not escape")
        self.delegate.append(event)

    def events_for(self, session_id: str) -> tuple[RuntimeEvent, ...]:
        return self.delegate.events_for(session_id)

    def state_for(self, session_id: str) -> SessionState:
        return self.delegate.state_for(session_id)

    def next_sequence(self, session_id: str) -> int:
        return self.delegate.next_sequence(session_id)


def test_close_append_failure_records_failed_closed_without_report() -> None:
    ledger = FailingCloseLedger(_released_ledger(), persistent=False)

    result = CloseSyntheticSession(
        ledger=ledger,
        snapshot=_snapshot(),
        evaluator=_evaluator(),
    ).execute(_command())

    assert result.failure_code is SyntheticSessionCloseFailureCode.LEDGER_FAILURE
    assert result.participant.final_answer is None
    assert result.evaluation is None
    assert result.runtime_event.event is SessionEvent.RUNTIME_FAILURE
    assert ledger.state_for("session-close-001") is SessionState.FAILED_CLOSED


def test_persistent_close_ledger_failure_raises_without_report() -> None:
    ledger = FailingCloseLedger(_released_ledger(), persistent=True)

    with pytest.raises(SessionCloseLedgerUnavailable, match="no report was released"):
        CloseSyntheticSession(
            ledger=ledger,
            snapshot=_snapshot(),
            evaluator=_evaluator(),
        ).execute(_command())

    assert ledger.delegate.state_for("session-close-001") is (
        SessionState.RESPONSE_RELEASED
    )


def test_exact_retry_is_detached_and_conflicting_retry_rejects() -> None:
    ledger = _released_ledger()
    closer = CloseSyntheticSession(
        ledger=ledger,
        snapshot=_snapshot(),
        evaluator=_evaluator(),
    )
    command = _command()

    first = closer.execute(command)
    second = closer.execute(command)

    assert first == second
    assert len(ledger.events_for(command.session_id)) == 5
    assert first.participant.final_answer is not None
    first.participant.final_answer.text = "tampered outside closer"
    assert (
        closer.execute(command).participant.final_answer
        == second.participant.final_answer
    )
    with pytest.raises(SessionCloseIdempotencyConflict):
        closer.execute(
            command.model_copy(update={"evidence_ids": ("changed-evidence",)})
        )
    assert len(ledger.events_for(command.session_id)) == 5


def test_bound_snapshot_is_detached_from_later_caller_mutation() -> None:
    snapshot = _snapshot()
    closer = CloseSyntheticSession(
        ledger=_released_ledger(),
        snapshot=snapshot,
        evaluator=_evaluator(),
    )
    snapshot.turns[1].text = "tampered outside closer"

    result = closer.execute(_command())

    assert result.participant.final_answer is not None
    assert result.participant.final_answer.text == (
        "[SYNTHETIC] What would feel useful to discuss?"
    )


def test_active_session_rejects_close_before_evaluation_or_append() -> None:
    ledger = InMemoryRuntimeEventLedger()
    ledger.bind_session("session-close-001", _config())
    ledger.append(
        _event(
            event_id="active-event-start",
            sequence=0,
            event=SessionEvent.START_SESSION,
            before=SessionState.CREATED,
            after=SessionState.ACTIVE,
            causation_id="session-close-001:create",
            evidence_ids=("scenario-synthetic-close",),
        )
    )

    class MustNotEvaluate:
        def evaluate_artifact(self, _artifact: object) -> TrajectoryEvaluationResult:
            raise AssertionError("evaluator must not be called")

    with pytest.raises(SessionCloseStateConflict, match="RESPONSE_RELEASED"):
        CloseSyntheticSession(
            ledger=ledger,
            snapshot=_snapshot(),
            evaluator=MustNotEvaluate(),
        ).execute(_command())
    assert len(ledger.events_for("session-close-001")) == 1


def test_close_models_are_strict_and_participant_projection_is_isolated() -> None:
    with pytest.raises(ValidationError, match="unexpected"):
        SyntheticSessionCloseCommand.model_validate(
            {**_command().model_dump(mode="json"), "unexpected": True}
        )
    with pytest.raises(ValidationError, match="unique"):
        SyntheticSessionCloseCommand(
            **{
                **_command().model_dump(),
                "evidence_ids": ("duplicate", "duplicate"),
            }
        )

    assert set(ParticipantSessionCloseView.model_fields) == {
        "contract_version",
        "request_id",
        "session_id",
        "status",
        "state",
        "trajectory_id",
        "final_answer",
    }
    assert set(ResearchSessionCloseView.model_fields) == {
        "contract_version",
        "participant",
        "evaluation",
        "runtime_event",
        "failure_code",
    }
    forbidden = {
        "trajectory",
        "final_answer_findings",
        "trajectory_findings",
        "runtime_event",
        "failure_code",
        "canonical_hash",
        "chain_of_thought",
        "risk_score",
        "diagnosis",
        "clinical_disposition",
    }
    assert forbidden.isdisjoint(ParticipantSessionCloseView.model_fields)
