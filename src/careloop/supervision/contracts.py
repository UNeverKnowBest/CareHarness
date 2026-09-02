"""Strict M15 contracts for the simulated research-review queue."""

from datetime import datetime
from enum import StrEnum
from typing import Protocol, Self

from pydantic import AwareDatetime, Field, model_validator

from careloop.agent_runtime import (
    ModelDraft,
    ReviewDecision,
    RuntimeEvent,
    SessionState,
)
from careloop.agent_runtime.contracts import (
    ContractVersion,
    NonBlankStr,
    NonEmptyStrings,
    RuntimeContractModel,
)


class ReviewQueueStatus(StrEnum):
    """Queue lifecycle values; these are not clinical dispositions."""

    PENDING = "pending"
    CLAIMED = "claimed"
    RESOLVED = "resolved"


class ReviewQueueItemV1(RuntimeContractModel):
    """Authoritative reviewer-only snapshot of one quarantined synthetic draft."""

    contract_version: ContractVersion
    review_id: NonBlankStr
    session_id: NonBlankStr
    request_id: NonBlankStr
    draft: ModelDraft
    locale: NonBlankStr
    status: ReviewQueueStatus
    revision: int = Field(ge=0)
    enqueued_at: AwareDatetime
    review_target_at: AwareDatetime
    claimed_by: NonBlankStr | None
    claimed_at: AwareDatetime | None
    resolved_at: AwareDatetime | None
    decision: ReviewDecision | None
    evidence_ids: NonEmptyStrings

    @model_validator(mode="after")
    def validate_queue_lifecycle(self) -> Self:
        if self.review_target_at < self.enqueued_at:
            raise ValueError("review_target_at must not precede enqueued_at")
        if len(set(self.evidence_ids)) != len(self.evidence_ids):
            raise ValueError("evidence_ids must be unique")
        if self.claimed_by is not None and not self.claimed_by.startswith(
            "synthetic-reviewer:"
        ):
            raise ValueError("claimed_by must identify a synthetic-reviewer")
        if self.claimed_at is not None and self.claimed_at < self.enqueued_at:
            raise ValueError("claimed_at must not precede enqueued_at")
        if self.resolved_at is not None:
            if self.claimed_at is None or self.resolved_at < self.claimed_at:
                raise ValueError("resolved_at must not precede claimed_at")

        if self.status is ReviewQueueStatus.PENDING:
            if self.revision != 0:
                raise ValueError("pending review must have revision zero")
            if any(
                value is not None
                for value in (
                    self.claimed_by,
                    self.claimed_at,
                    self.resolved_at,
                    self.decision,
                )
            ):
                raise ValueError("pending review cannot contain claim or resolution")
        elif self.status is ReviewQueueStatus.CLAIMED:
            if self.revision < 1 or self.claimed_by is None or self.claimed_at is None:
                raise ValueError("claimed review requires claimant, time, and revision")
            if self.resolved_at is not None or self.decision is not None:
                raise ValueError("claimed review cannot contain resolution")
        else:
            if (
                self.revision < 2
                or self.claimed_by is None
                or self.claimed_at is None
                or self.resolved_at is None
                or self.decision is None
            ):
                raise ValueError("resolved review requires complete decision evidence")
        return self


class ReviewQueueAuditV1(RuntimeContractModel):
    """Deterministic descriptive queue counts derived at an explicit instant."""

    contract_version: ContractVersion
    as_of: AwareDatetime
    pending_count: int = Field(ge=0)
    claimed_count: int = Field(ge=0)
    resolved_count: int = Field(ge=0)
    over_target_review_ids: tuple[NonBlankStr, ...]
    within_target_resolution_ids: tuple[NonBlankStr, ...]
    after_target_resolution_ids: tuple[NonBlankStr, ...]


class ReviewQueuePort(Protocol):
    """Persistence boundary used by M15 orchestration."""

    def enqueue_review(self, item: ReviewQueueItemV1) -> ReviewQueueItemV1: ...


class ReviewResolutionStorePort(Protocol):
    """Atomic authoritative boundary for a simulated review decision."""

    def review_item(self, review_id: str) -> ReviewQueueItemV1: ...

    def events_for(self, session_id: str) -> tuple[RuntimeEvent, ...]: ...

    def state_for(self, session_id: str) -> SessionState: ...

    def next_sequence(self, session_id: str) -> int: ...

    def append_review_resolution(
        self,
        event: RuntimeEvent,
        *,
        review_id: str,
        reviewer_id: str,
        expected_revision: int,
        decision: ReviewDecision,
        resolved_at: datetime,
        evidence_ids: tuple[str, ...],
    ) -> ReviewQueueItemV1: ...


def require_aware(value: datetime, *, field_name: str) -> datetime:
    """Reject implicit local time at application/storage boundaries."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must include a timezone")
    return value
