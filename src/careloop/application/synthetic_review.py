"""Deterministic M11 resolution of one synthetic pre-release review hold."""

from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator

from careloop.agent_runtime import (
    ModelDraft,
    ReviewDecision,
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
from careloop.domain import Turn


class SyntheticReviewStatus(StrEnum):
    """Participant-safe outcome of one synthetic review resolution."""

    APPROVED_RELEASED = "approved_released"
    REPLACEMENT_RELEASED = "replacement_released"
    HANDED_OFF = "handed_off"
    REJECTED = "rejected"
    FAILED_CLOSED = "failed_closed"


class SyntheticReviewFailureCode(StrEnum):
    """Stable review-resolution failure categories."""

    LEDGER_FAILURE = "ledger_failure"


class SyntheticReviewContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class SyntheticReviewCommand(SyntheticReviewContractModel):
    """Strict reviewer-only input for one held synthetic draft."""

    contract_version: ContractVersion
    request_id: NonBlankStr
    session_id: NonBlankStr
    decision: ReviewDecision
    reviewed_draft: ModelDraft
    release_turn: Turn | None
    evidence_ids: NonEmptyStrings

    @model_validator(mode="after")
    def validate_decision_shape(self) -> Self:
        if len(set(self.evidence_ids)) != len(self.evidence_ids):
            raise ValueError("evidence_ids must be unique")
        releases = self.decision in {
            ReviewDecision.APPROVE,
            ReviewDecision.REPLACE_WITH_SAFE_TEMPLATE,
        }
        if releases:
            if self.release_turn is None:
                raise ValueError("release decision requires release_turn")
            if self.release_turn.role != "assistant":
                raise ValueError("release_turn must have the assistant role")
            if not self.release_turn.text.strip():
                raise ValueError("release_turn text must not be empty or whitespace")
        elif self.release_turn is not None:
            raise ValueError("HANDOFF and REJECT require release_turn=None")
        if (
            self.decision is ReviewDecision.APPROVE
            and self.release_turn is not None
            and self.release_turn.text != self.reviewed_draft.text
        ):
            raise ValueError("APPROVE release text must exactly match reviewed draft")
        return self


class ParticipantReviewView(SyntheticReviewContractModel):
    """Participant projection without quarantined review evidence."""

    contract_version: ContractVersion
    request_id: NonBlankStr
    session_id: NonBlankStr
    status: SyntheticReviewStatus
    state: SessionState
    released_turn: Turn | None

    @model_validator(mode="after")
    def validate_projection(self) -> Self:
        released = self.status in {
            SyntheticReviewStatus.APPROVED_RELEASED,
            SyntheticReviewStatus.REPLACEMENT_RELEASED,
        }
        if released:
            if self.state is not SessionState.RESPONSE_RELEASED:
                raise ValueError("released review requires RESPONSE_RELEASED")
            if self.released_turn is None or self.released_turn.role != "assistant":
                raise ValueError("released review requires one assistant turn")
        elif self.released_turn is not None:
            raise ValueError("non-release review status cannot contain released_turn")
        if (
            self.status
            in {
                SyntheticReviewStatus.HANDED_OFF,
                SyntheticReviewStatus.REJECTED,
            }
            and self.state is not SessionState.CLOSED
        ):
            raise ValueError("handoff and rejection require CLOSED")
        if (
            self.status is SyntheticReviewStatus.FAILED_CLOSED
            and self.state is not SessionState.FAILED_CLOSED
        ):
            raise ValueError("failed_closed requires FAILED_CLOSED")
        return self


class ResearchReviewResolutionView(SyntheticReviewContractModel):
    """Research-review result retaining draft and append-only evidence."""

    contract_version: ContractVersion
    participant: ParticipantReviewView
    decision: ReviewDecision
    reviewed_draft: ModelDraft
    runtime_event: RuntimeEvent
    failure_code: SyntheticReviewFailureCode | None

    @model_validator(mode="after")
    def validate_result(self) -> Self:
        if self.runtime_event.session_id != self.participant.session_id:
            raise ValueError("runtime_event and participant session must match")
        if self.runtime_event.state_after is not self.participant.state:
            raise ValueError("runtime_event and participant state must match")
        failed = self.participant.status is SyntheticReviewStatus.FAILED_CLOSED
        if failed != (self.failure_code is not None):
            raise ValueError("failure_code must exist exactly for failed_closed")
        if failed:
            if self.runtime_event.event is not SessionEvent.RUNTIME_FAILURE:
                raise ValueError("failed resolution requires RUNTIME_FAILURE")
        else:
            expected_event = _DECISION_EVENTS[self.decision]
            expected_status = _DECISION_STATUSES[self.decision]
            if self.runtime_event.event is not expected_event:
                raise ValueError("runtime_event must match review decision")
            if self.participant.status is not expected_status:
                raise ValueError("participant status must match review decision")
        return self


class ReviewIdempotencyConflict(ValueError):
    """Raised when a review request identity is reused with changed content."""


class ReviewStateConflict(ValueError):
    """Raised when a review does not match the current held ledger evidence."""


class ReviewLedgerUnavailable(RuntimeError):
    """Raised when neither a review nor its failure transition can be appended."""


_DECISION_EVENTS = {
    ReviewDecision.APPROVE: SessionEvent.REVIEW_APPROVED,
    ReviewDecision.REPLACE_WITH_SAFE_TEMPLATE: SessionEvent.REVIEW_REPLACED,
    ReviewDecision.HANDOFF: SessionEvent.REVIEW_HANDOFF,
    ReviewDecision.REJECT: SessionEvent.REVIEW_REJECTED,
}

_DECISION_STATUSES = {
    ReviewDecision.APPROVE: SyntheticReviewStatus.APPROVED_RELEASED,
    ReviewDecision.REPLACE_WITH_SAFE_TEMPLATE: (
        SyntheticReviewStatus.REPLACEMENT_RELEASED
    ),
    ReviewDecision.HANDOFF: SyntheticReviewStatus.HANDED_OFF,
    ReviewDecision.REJECT: SyntheticReviewStatus.REJECTED,
}


class ResolveSyntheticReview:
    """Resolve one held synthetic draft only after append-only evidence persists."""

    def __init__(
        self,
        *,
        ledger: RuntimeEventLedgerPort,
        held_draft: ModelDraft,
    ) -> None:
        self._ledger = ledger
        self._held_draft = ModelDraft.model_validate(held_draft.model_dump())
        self._results: dict[
            tuple[str, str],
            tuple[SyntheticReviewCommand, ResearchReviewResolutionView],
        ] = {}

    def execute(self, command: SyntheticReviewCommand) -> ResearchReviewResolutionView:
        command = SyntheticReviewCommand.model_validate(command.model_dump())
        key = (command.session_id, command.request_id)
        cached = self._results.get(key)
        if cached is not None:
            prior_command, prior_result = cached
            if prior_command != command:
                raise ReviewIdempotencyConflict(
                    "review request identity has conflicting content"
                )
            return self._result_snapshot(prior_result)

        self._validate_held_draft(command)
        event = self._decision_event(command)
        try:
            self._ledger.append(event)
        except Exception:
            result = self._fail_closed(command)
            return self._remember(command, result)

        result = self._result(
            command,
            status=_DECISION_STATUSES[command.decision],
            runtime_event=event,
            released_turn=command.release_turn,
        )
        return self._remember(command, result)

    def _validate_held_draft(self, command: SyntheticReviewCommand) -> None:
        if command.reviewed_draft != self._held_draft:
            raise ReviewStateConflict(
                "reviewed draft does not match authoritative held draft"
            )
        try:
            state = self._ledger.state_for(command.session_id)
            events = self._ledger.events_for(command.session_id)
        except Exception as error:
            raise ReviewStateConflict(
                "review session is unavailable or not bound"
            ) from error
        if state is not SessionState.AWAITING_HUMAN_REVIEW:
            raise ReviewStateConflict(
                "review requires AWAITING_HUMAN_REVIEW ledger state"
            )
        if not events or events[-1].event is not SessionEvent.DRAFT_HELD_FOR_REVIEW:
            raise ReviewStateConflict("last ledger event must hold a draft for review")
        held = events[-1]
        draft_id = command.reviewed_draft.draft_id
        if held.causation_id != draft_id:
            raise ReviewStateConflict("reviewed draft does not match held causation")
        if not held.evidence_ids or held.evidence_ids[0] != draft_id:
            raise ReviewStateConflict("reviewed draft does not match held evidence")

    def _decision_event(self, command: SyntheticReviewCommand) -> RuntimeEvent:
        event = _DECISION_EVENTS[command.decision]
        before = SessionState.AWAITING_HUMAN_REVIEW
        release_evidence = (
            () if command.release_turn is None else (command.release_turn.turn_id,)
        )
        return RuntimeEvent(
            contract_version="v1",
            event_id=(
                f"{command.session_id}:{command.request_id}:review:"
                f"{event.value.casefold()}"
            ),
            session_id=command.session_id,
            sequence=self._ledger.next_sequence(command.session_id),
            event=event,
            state_before=before,
            state_after=transition_session(before, event),
            causation_id=command.request_id,
            evidence_ids=(command.reviewed_draft.draft_id,)
            + command.evidence_ids
            + release_evidence,
        )

    def _fail_closed(
        self, command: SyntheticReviewCommand
    ) -> ResearchReviewResolutionView:
        before = self._ledger.state_for(command.session_id)
        failure = RuntimeEvent(
            contract_version="v1",
            event_id=(
                f"{command.session_id}:{command.request_id}:review:"
                "failure:ledger_failure"
            ),
            session_id=command.session_id,
            sequence=self._ledger.next_sequence(command.session_id),
            event=SessionEvent.RUNTIME_FAILURE,
            state_before=before,
            state_after=transition_session(before, SessionEvent.RUNTIME_FAILURE),
            causation_id=command.request_id,
            evidence_ids=("synthetic_review:ledger_failure",),
        )
        try:
            self._ledger.append(failure)
        except Exception as error:
            raise ReviewLedgerUnavailable(
                "review failure could not be appended; no output was released"
            ) from error
        return self._result(
            command,
            status=SyntheticReviewStatus.FAILED_CLOSED,
            runtime_event=failure,
            released_turn=None,
            failure_code=SyntheticReviewFailureCode.LEDGER_FAILURE,
        )

    def _result(
        self,
        command: SyntheticReviewCommand,
        *,
        status: SyntheticReviewStatus,
        runtime_event: RuntimeEvent,
        released_turn: Turn | None,
        failure_code: SyntheticReviewFailureCode | None = None,
    ) -> ResearchReviewResolutionView:
        participant = ParticipantReviewView(
            contract_version="v1",
            request_id=command.request_id,
            session_id=command.session_id,
            status=status,
            state=runtime_event.state_after,
            released_turn=released_turn,
        )
        return ResearchReviewResolutionView(
            contract_version="v1",
            participant=participant,
            decision=command.decision,
            reviewed_draft=command.reviewed_draft,
            runtime_event=runtime_event,
            failure_code=failure_code,
        )

    def _remember(
        self,
        command: SyntheticReviewCommand,
        result: ResearchReviewResolutionView,
    ) -> ResearchReviewResolutionView:
        command_snapshot = SyntheticReviewCommand.model_validate(command.model_dump())
        result_snapshot = self._result_snapshot(result)
        self._results[(command.session_id, command.request_id)] = (
            command_snapshot,
            result_snapshot,
        )
        return self._result_snapshot(result_snapshot)

    @staticmethod
    def _result_snapshot(
        result: ResearchReviewResolutionView,
    ) -> ResearchReviewResolutionView:
        return ResearchReviewResolutionView.model_validate(result.model_dump())
