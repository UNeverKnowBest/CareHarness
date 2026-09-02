"""M15 composition of quarantined turn execution and durable review enqueue."""

from datetime import datetime
from typing import Protocol, Self

from pydantic import model_validator

from careloop.agent_runtime.contracts import (
    ContractVersion,
    RuntimeContractModel,
)
from careloop.application.synthetic_turn import (
    ResearchReviewTurnView,
    SyntheticTurnCommand,
    SyntheticTurnStatus,
)
from careloop.supervision.contracts import (
    ReviewQueueItemV1,
    ReviewQueuePort,
    ReviewQueueStatus,
    require_aware,
)


class SyntheticTurnRunner(Protocol):
    async def execute(
        self, command: SyntheticTurnCommand
    ) -> ResearchReviewTurnView: ...


class SupervisedTurnResultV1(RuntimeContractModel):
    """Reviewer-side result; participant data remains nested in the M10 view."""

    contract_version: ContractVersion
    turn: ResearchReviewTurnView
    review_item: ReviewQueueItemV1 | None

    @model_validator(mode="after")
    def validate_hold_correlation(self) -> Self:
        held = self.turn.participant.status is SyntheticTurnStatus.AWAITING_HUMAN_REVIEW
        if held != (self.review_item is not None):
            raise ValueError("review_item must exist exactly for a held draft")
        if self.turn.participant.status is not SyntheticTurnStatus.RELEASED:
            if self.turn.participant.released_turn is not None:
                raise ValueError("non-release supervision result cannot expose a reply")
        if self.review_item is not None:
            if not self.turn.quarantined_drafts:
                raise ValueError("held result requires a quarantined draft")
            if self.review_item.session_id != self.turn.participant.session_id:
                raise ValueError("review item session must match turn result")
            if self.review_item.request_id != self.turn.participant.request_id:
                raise ValueError("review item request must match turn result")
            if self.review_item.draft != self.turn.quarantined_drafts[-1]:
                raise ValueError("review item must retain the final quarantined draft")
        return self


class SupervisedSyntheticTurn:
    """Queue only exhausted/explicit holds after the durable lifecycle append."""

    def __init__(
        self,
        *,
        runner: SyntheticTurnRunner,
        review_queue: ReviewQueuePort,
        locale: str,
    ) -> None:
        if not locale.strip():
            raise ValueError("locale must not be empty or whitespace")
        self._runner = runner
        self._review_queue = review_queue
        self._locale = locale

    async def execute(
        self,
        command: SyntheticTurnCommand,
        *,
        enqueued_at: datetime,
        review_target_at: datetime,
    ) -> SupervisedTurnResultV1:
        require_aware(enqueued_at, field_name="enqueued_at")
        require_aware(review_target_at, field_name="review_target_at")
        result = await self._runner.execute(command)
        review_item: ReviewQueueItemV1 | None = None
        if result.participant.status is SyntheticTurnStatus.AWAITING_HUMAN_REVIEW:
            final_draft = result.quarantined_drafts[-1]
            final_gate = result.draft_gate_results[-1]
            review_item = ReviewQueueItemV1(
                contract_version="v1",
                review_id=(
                    f"{result.participant.session_id}:"
                    f"{result.participant.request_id}:review"
                ),
                session_id=result.participant.session_id,
                request_id=result.participant.request_id,
                draft=final_draft,
                locale=self._locale,
                status=ReviewQueueStatus.PENDING,
                revision=0,
                enqueued_at=enqueued_at,
                review_target_at=review_target_at,
                claimed_by=None,
                claimed_at=None,
                resolved_at=None,
                decision=None,
                evidence_ids=(final_draft.draft_id,) + final_gate.finding_ids,
            )
            review_item = self._review_queue.enqueue_review(review_item)
        return SupervisedTurnResultV1(
            contract_version="v1",
            turn=result,
            review_item=review_item,
        )
