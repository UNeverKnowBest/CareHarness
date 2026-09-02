"""Atomic M15 composition of M11 review resolution and durable queue state."""

from typing import Self

from pydantic import AwareDatetime, Field, model_validator

from careloop.agent_runtime import (
    ReviewDecision,
    RuntimeEvent,
    SessionEvent,
    SessionState,
    transition_session,
)
from careloop.agent_runtime.contracts import (
    ContractVersion,
    NonBlankStr,
    RuntimeContractModel,
)
from careloop.application.synthetic_review import (
    ParticipantReviewView,
    ResearchReviewResolutionView,
    SyntheticReviewCommand,
    SyntheticReviewStatus,
)
from careloop.supervision.contracts import (
    ReviewQueueItemV1,
    ReviewQueueStatus,
    ReviewResolutionStorePort,
    require_aware,
)


class QueuedSyntheticReviewCommand(RuntimeContractModel):
    """One revision-pinned decision over a claimed synthetic queue item."""

    contract_version: ContractVersion
    review_id: NonBlankStr
    reviewer_id: NonBlankStr
    expected_revision: int = Field(ge=1)
    resolved_at: AwareDatetime
    review: SyntheticReviewCommand

    @model_validator(mode="after")
    def validate_synthetic_reviewer(self) -> Self:
        if not self.reviewer_id.startswith("synthetic-reviewer:"):
            raise ValueError("reviewer_id must identify a synthetic-reviewer")
        return self


class QueuedReviewResolutionV1(RuntimeContractModel):
    contract_version: ContractVersion
    resolution: ResearchReviewResolutionView
    queue_item: ReviewQueueItemV1

    @model_validator(mode="after")
    def validate_correlated_resolution(self) -> Self:
        if self.queue_item.status is not ReviewQueueStatus.RESOLVED:
            raise ValueError("queue_item must be resolved")
        if self.queue_item.decision is not self.resolution.decision:
            raise ValueError("queue decision must match runtime resolution")
        if self.queue_item.session_id != self.resolution.participant.session_id:
            raise ValueError("queue and runtime sessions must match")
        return self


class ResolveQueuedSyntheticReview:
    """Commit decision event, outbox, state, and queue revision atomically."""

    def __init__(self, *, store: ReviewResolutionStorePort) -> None:
        self._store = store

    def execute(
        self, command: QueuedSyntheticReviewCommand
    ) -> QueuedReviewResolutionV1:
        command = QueuedSyntheticReviewCommand.model_validate(command.model_dump())
        require_aware(command.resolved_at, field_name="resolved_at")
        item = self._store.review_item(command.review_id)
        if item.session_id != command.review.session_id:
            raise ValueError("review command session does not match queue item")
        if item.draft != command.review.reviewed_draft:
            raise ValueError("reviewed draft does not match queue item")
        if (
            self._store.state_for(item.session_id)
            is not SessionState.AWAITING_HUMAN_REVIEW
        ):
            raise ValueError("session is not awaiting simulated review")
        events = self._store.events_for(item.session_id)
        if (
            not events
            or events[-1].event is not SessionEvent.DRAFT_HELD_FOR_REVIEW
            or item.draft.draft_id not in events[-1].evidence_ids
        ):
            raise ValueError("authoritative held-draft evidence does not match queue")

        event_type, status = _DECISION_EVENTS[command.review.decision]
        release = command.review.release_turn
        release_evidence = () if release is None else (release.turn_id,)
        before = SessionState.AWAITING_HUMAN_REVIEW
        event = RuntimeEvent(
            contract_version="v1",
            event_id=(
                f"{item.session_id}:{command.review.request_id}:review:"
                f"{event_type.value.casefold()}"
            ),
            session_id=item.session_id,
            sequence=self._store.next_sequence(item.session_id),
            event=event_type,
            state_before=before,
            state_after=transition_session(before, event_type),
            causation_id=command.review.request_id,
            evidence_ids=(item.draft.draft_id,)
            + command.review.evidence_ids
            + release_evidence,
        )
        resolved_item = self._store.append_review_resolution(
            event,
            review_id=command.review_id,
            reviewer_id=command.reviewer_id,
            expected_revision=command.expected_revision,
            decision=command.review.decision,
            resolved_at=command.resolved_at,
            evidence_ids=command.review.evidence_ids,
        )
        participant = ParticipantReviewView(
            contract_version="v1",
            request_id=command.review.request_id,
            session_id=item.session_id,
            status=status,
            state=event.state_after,
            released_turn=release,
        )
        resolution = ResearchReviewResolutionView(
            contract_version="v1",
            participant=participant,
            decision=command.review.decision,
            reviewed_draft=item.draft,
            runtime_event=event,
            failure_code=None,
        )
        return QueuedReviewResolutionV1(
            contract_version="v1",
            resolution=resolution,
            queue_item=resolved_item,
        )


_DECISION_EVENTS = {
    ReviewDecision.APPROVE: (
        SessionEvent.REVIEW_APPROVED,
        SyntheticReviewStatus.APPROVED_RELEASED,
    ),
    ReviewDecision.REPLACE_WITH_SAFE_TEMPLATE: (
        SessionEvent.REVIEW_REPLACED,
        SyntheticReviewStatus.REPLACEMENT_RELEASED,
    ),
    ReviewDecision.HANDOFF: (
        SessionEvent.REVIEW_HANDOFF,
        SyntheticReviewStatus.HANDED_OFF,
    ),
    ReviewDecision.REJECT: (
        SessionEvent.REVIEW_REJECTED,
        SyntheticReviewStatus.REJECTED,
    ),
}
