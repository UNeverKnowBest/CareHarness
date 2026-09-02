"""Deterministic M12 close and evaluation of one synthetic session."""

from enum import StrEnum
from typing import Protocol, Self

from pydantic import BaseModel, ConfigDict, model_validator

from careloop.agent_runtime import (
    RuntimeEvent,
    RuntimeEventLedgerPort,
    SessionEvent,
    SessionState,
    transition_session,
)
from careloop.agent_runtime.contracts import (
    ContractVersion,
    NonBlankStr,
    NonEmptyStrings,
)
from careloop.artifacts import (
    FrozenTrajectoryArtifact,
    build_frozen_trajectory_artifact,
)
from careloop.domain import (
    FinalAnswerView,
    ProcessMarker,
    SafetyEvent,
    Trajectory,
    Turn,
)
from careloop.evaluation import TrajectoryEvaluationResult


class SyntheticSessionCloseStatus(StrEnum):
    """Participant-safe outcomes of one synthetic close request."""

    EVALUATED = "evaluated"
    FAILED_CLOSED = "failed_closed"


class SyntheticSessionCloseFailureCode(StrEnum):
    """Stable close failure categories without exception details."""

    EVALUATION_FAILURE = "evaluation_failure"
    LEDGER_FAILURE = "ledger_failure"


class SyntheticSessionCloseContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class SyntheticSessionSnapshot(SyntheticSessionCloseContractModel):
    """Detached authoritative synthetic transcript and evidence snapshot."""

    contract_version: ContractVersion
    session_id: NonBlankStr
    trajectory_id: NonBlankStr
    turns: tuple[Turn, ...]
    process_markers: tuple[ProcessMarker, ...]
    safety_events: tuple[SafetyEvent, ...]

    @model_validator(mode="after")
    def validate_trajectory_shape(self) -> Self:
        trajectory = self.trajectory()
        if not any(turn.role == "assistant" for turn in trajectory.turns):
            raise ValueError("synthetic close requires a released assistant turn")
        user_ids = {turn.turn_id for turn in trajectory.turns if turn.role == "user"}
        if any(
            triggering_id not in user_ids
            for event in trajectory.safety_events
            for triggering_id in event.triggering_turn_ids
        ):
            raise ValueError("safety events must reference synthetic user turns")
        return self

    def trajectory(self) -> Trajectory:
        """Build a detached validated trajectory from the bound snapshot."""
        return Trajectory(
            trajectory_schema_version="v1",
            trajectory_id=self.trajectory_id,
            turns=tuple(Turn.model_validate(turn.model_dump()) for turn in self.turns),
            process_markers=tuple(
                ProcessMarker.model_validate(marker.model_dump())
                for marker in self.process_markers
            ),
            safety_events=tuple(
                SafetyEvent.model_validate(event.model_dump())
                for event in self.safety_events
            ),
        )


class SyntheticSessionCloseCommand(SyntheticSessionCloseContractModel):
    """Strict identity and evidence for one synthetic close request."""

    contract_version: ContractVersion
    request_id: NonBlankStr
    session_id: NonBlankStr
    trajectory_id: NonBlankStr
    evidence_ids: NonEmptyStrings

    @model_validator(mode="after")
    def validate_unique_evidence(self) -> Self:
        if len(set(self.evidence_ids)) != len(self.evidence_ids):
            raise ValueError("evidence_ids must be unique")
        return self


class ParticipantSessionCloseView(SyntheticSessionCloseContractModel):
    """Participant projection without raw trajectory or evaluation evidence."""

    contract_version: ContractVersion
    request_id: NonBlankStr
    session_id: NonBlankStr
    status: SyntheticSessionCloseStatus
    state: SessionState
    trajectory_id: NonBlankStr
    final_answer: FinalAnswerView | None

    @model_validator(mode="after")
    def validate_projection(self) -> Self:
        if self.status is SyntheticSessionCloseStatus.EVALUATED:
            if self.state is not SessionState.CLOSED:
                raise ValueError("evaluated close requires CLOSED")
            if self.final_answer is None:
                raise ValueError("evaluated close requires final_answer")
        else:
            if self.state is not SessionState.FAILED_CLOSED:
                raise ValueError("failed close requires FAILED_CLOSED")
            if self.final_answer is not None:
                raise ValueError("failed close cannot contain final_answer")
        return self


class ResearchSessionCloseView(SyntheticSessionCloseContractModel):
    """Research result retaining raw evaluation and append-only evidence."""

    contract_version: ContractVersion
    participant: ParticipantSessionCloseView
    evaluation: TrajectoryEvaluationResult | None
    runtime_event: RuntimeEvent
    failure_code: SyntheticSessionCloseFailureCode | None

    @model_validator(mode="after")
    def validate_result(self) -> Self:
        if self.runtime_event.session_id != self.participant.session_id:
            raise ValueError("runtime_event and participant session must match")
        if self.runtime_event.state_after is not self.participant.state:
            raise ValueError("runtime_event and participant state must match")
        failed = self.participant.status is SyntheticSessionCloseStatus.FAILED_CLOSED
        if failed:
            if self.evaluation is not None or self.failure_code is None:
                raise ValueError("failed close requires only a failure category")
            if self.runtime_event.event is not SessionEvent.RUNTIME_FAILURE:
                raise ValueError("failed close requires RUNTIME_FAILURE")
        else:
            if self.evaluation is None or self.failure_code is not None:
                raise ValueError("evaluated close requires one evaluation")
            if self.runtime_event.event is not SessionEvent.CLOSE_SESSION:
                raise ValueError("evaluated close requires CLOSE_SESSION")
            if self.evaluation.case_id != self.participant.trajectory_id:
                raise ValueError("evaluation and participant trajectory must match")
            if self.evaluation.final_answer != self.participant.final_answer:
                raise ValueError("evaluation and participant final answer must match")
        return self


class SessionCloseIdempotencyConflict(ValueError):
    """Raised when a close request identity is reused with changed content."""


class SessionCloseStateConflict(ValueError):
    """Raised when a close request does not match authoritative evidence."""


class SessionCloseLedgerUnavailable(RuntimeError):
    """Raised when neither close nor its failure transition can be appended."""


class InMemoryArtifactEvaluator(Protocol):
    def evaluate_artifact(
        self,
        artifact: FrozenTrajectoryArtifact,
    ) -> TrajectoryEvaluationResult: ...


class CloseSyntheticSession:
    """Assemble, evaluate, and close one evidence-linked synthetic session."""

    def __init__(
        self,
        *,
        ledger: RuntimeEventLedgerPort,
        snapshot: SyntheticSessionSnapshot,
        evaluator: InMemoryArtifactEvaluator,
    ) -> None:
        self._ledger = ledger
        self._snapshot = SyntheticSessionSnapshot.model_validate(snapshot.model_dump())
        self._evaluator = evaluator
        self._results: dict[
            tuple[str, str],
            tuple[SyntheticSessionCloseCommand, ResearchSessionCloseView],
        ] = {}

    def execute(
        self,
        command: SyntheticSessionCloseCommand,
    ) -> ResearchSessionCloseView:
        command = SyntheticSessionCloseCommand.model_validate(command.model_dump())
        key = (command.session_id, command.request_id)
        cached = self._results.get(key)
        if cached is not None:
            prior_command, prior_result = cached
            if prior_command != command:
                raise SessionCloseIdempotencyConflict(
                    "close request identity has conflicting content"
                )
            return self._result_snapshot(prior_result)

        events = self._validate_current_session(command)
        trajectory = self._snapshot.trajectory()
        self._validate_turn_evidence(trajectory, events)
        artifact = build_frozen_trajectory_artifact(
            case_id=trajectory.trajectory_id,
            trajectory=trajectory,
        )
        try:
            raw_evaluation = self._evaluator.evaluate_artifact(artifact)
            evaluation = TrajectoryEvaluationResult.model_validate(
                raw_evaluation.model_dump()
            )
            self._validate_evaluation(artifact, evaluation)
        except Exception:
            result = self._fail_closed(
                command,
                SyntheticSessionCloseFailureCode.EVALUATION_FAILURE,
            )
            return self._remember(command, result)

        close_event = self._close_event(command, evaluation)
        try:
            self._ledger.append(close_event)
        except Exception:
            result = self._fail_closed(
                command,
                SyntheticSessionCloseFailureCode.LEDGER_FAILURE,
            )
            return self._remember(command, result)

        result = self._result(
            command,
            runtime_event=close_event,
            evaluation=evaluation,
        )
        return self._remember(command, result)

    def _validate_current_session(
        self,
        command: SyntheticSessionCloseCommand,
    ) -> tuple[RuntimeEvent, ...]:
        if command.session_id != self._snapshot.session_id:
            raise SessionCloseStateConflict("close session does not match snapshot")
        if command.trajectory_id != self._snapshot.trajectory_id:
            raise SessionCloseStateConflict("close trajectory does not match snapshot")
        try:
            state = self._ledger.state_for(command.session_id)
            events = self._ledger.events_for(command.session_id)
        except Exception as error:
            raise SessionCloseStateConflict(
                "close session is unavailable or not bound"
            ) from error
        if state is not SessionState.RESPONSE_RELEASED:
            raise SessionCloseStateConflict(
                "synthetic evaluation close requires RESPONSE_RELEASED"
            )
        return events

    @staticmethod
    def _validate_turn_evidence(
        trajectory: Trajectory,
        events: tuple[RuntimeEvent, ...],
    ) -> None:
        user_ids = {turn.turn_id for turn in trajectory.turns if turn.role == "user"}
        assistant_ids = {
            turn.turn_id for turn in trajectory.turns if turn.role == "assistant"
        }
        submitted_ids: set[str] = set()
        released_ids: set[str] = set()
        last_submitted_id: str | None = None
        for event in events:
            if event.event is SessionEvent.SUBMIT_TURN and event.evidence_ids:
                last_submitted_id = event.evidence_ids[0]
                submitted_ids.add(last_submitted_id)
            elif event.event is SessionEvent.DRAFT_APPROVED:
                if last_submitted_id is not None:
                    released_ids.add(f"{last_submitted_id}:assistant")
            elif event.event in {
                SessionEvent.REVIEW_APPROVED,
                SessionEvent.REVIEW_REPLACED,
            }:
                released_ids.update(assistant_ids.intersection(event.evidence_ids))

        override_ids = {
            turn_id
            for event in trajectory.safety_events
            if event.requires_override and event.normal_flow_suppressed
            for turn_id in event.triggering_turn_ids
        }
        missing_users = user_ids - submitted_ids - override_ids
        omitted_users = submitted_ids - user_ids
        missing_assistants = assistant_ids - released_ids
        if missing_users or omitted_users or missing_assistants:
            raise SessionCloseStateConflict(
                "trajectory turns do not match submitted, override, "
                "and release evidence"
            )

    @staticmethod
    def _validate_evaluation(
        artifact: FrozenTrajectoryArtifact,
        evaluation: TrajectoryEvaluationResult,
    ) -> None:
        if evaluation.case_id != artifact.case_id:
            raise ValueError("evaluation case_id does not match artifact")
        if evaluation.canonical_hash != artifact.canonical_hash:
            raise ValueError("evaluation canonical_hash does not match artifact")
        if evaluation.trajectory != artifact.trajectory:
            raise ValueError("evaluation trajectory does not match artifact")

    def _close_event(
        self,
        command: SyntheticSessionCloseCommand,
        evaluation: TrajectoryEvaluationResult,
    ) -> RuntimeEvent:
        before = SessionState.RESPONSE_RELEASED
        return RuntimeEvent(
            contract_version="v1",
            event_id=f"{command.session_id}:{command.request_id}:close",
            session_id=command.session_id,
            sequence=self._ledger.next_sequence(command.session_id),
            event=SessionEvent.CLOSE_SESSION,
            state_before=before,
            state_after=transition_session(before, SessionEvent.CLOSE_SESSION),
            causation_id=command.request_id,
            evidence_ids=(
                evaluation.case_id,
                evaluation.canonical_hash,
            )
            + command.evidence_ids,
        )

    def _fail_closed(
        self,
        command: SyntheticSessionCloseCommand,
        code: SyntheticSessionCloseFailureCode,
    ) -> ResearchSessionCloseView:
        before = self._ledger.state_for(command.session_id)
        failure = RuntimeEvent(
            contract_version="v1",
            event_id=(
                f"{command.session_id}:{command.request_id}:close:failure:{code.value}"
            ),
            session_id=command.session_id,
            sequence=self._ledger.next_sequence(command.session_id),
            event=SessionEvent.RUNTIME_FAILURE,
            state_before=before,
            state_after=transition_session(before, SessionEvent.RUNTIME_FAILURE),
            causation_id=command.request_id,
            evidence_ids=(f"synthetic_session_close:{code.value}",),
        )
        try:
            self._ledger.append(failure)
        except Exception as error:
            raise SessionCloseLedgerUnavailable(
                "session close failure could not be appended; no report was released"
            ) from error
        return self._result(
            command,
            runtime_event=failure,
            evaluation=None,
            failure_code=code,
        )

    def _result(
        self,
        command: SyntheticSessionCloseCommand,
        *,
        runtime_event: RuntimeEvent,
        evaluation: TrajectoryEvaluationResult | None,
        failure_code: SyntheticSessionCloseFailureCode | None = None,
    ) -> ResearchSessionCloseView:
        status = (
            SyntheticSessionCloseStatus.EVALUATED
            if evaluation is not None
            else SyntheticSessionCloseStatus.FAILED_CLOSED
        )
        participant = ParticipantSessionCloseView(
            contract_version="v1",
            request_id=command.request_id,
            session_id=command.session_id,
            status=status,
            state=runtime_event.state_after,
            trajectory_id=command.trajectory_id,
            final_answer=None if evaluation is None else evaluation.final_answer,
        )
        return ResearchSessionCloseView(
            contract_version="v1",
            participant=participant,
            evaluation=evaluation,
            runtime_event=runtime_event,
            failure_code=failure_code,
        )

    def _remember(
        self,
        command: SyntheticSessionCloseCommand,
        result: ResearchSessionCloseView,
    ) -> ResearchSessionCloseView:
        command_snapshot = SyntheticSessionCloseCommand.model_validate(
            command.model_dump()
        )
        result_snapshot = self._result_snapshot(result)
        self._results[(command.session_id, command.request_id)] = (
            command_snapshot,
            result_snapshot,
        )
        return self._result_snapshot(result_snapshot)

    @staticmethod
    def _result_snapshot(result: ResearchSessionCloseView) -> ResearchSessionCloseView:
        return ResearchSessionCloseView.model_validate(result.model_dump())
