"""Strict participant-safe M16 HTTP and SSE contracts."""

from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import AwareDatetime, Field, JsonValue, model_validator

from careloop.agent_runtime.contracts import (
    ContractVersion,
    NonBlankStr,
    NonEmptyStrings,
    ReviewDecision,
    RuntimeContractModel,
)
from careloop.domain import Turn


class ReleaseDispositionV1(StrEnum):
    """Release control only; never a condition or clinical classification."""

    ALLOW = "allow"
    HOLD_FOR_REVIEW = "hold_for_review"
    SYSTEM_FAILURE = "system_failure"


class PublicSessionStateV1(StrEnum):
    """Coarse participant-safe state without draft or gate details."""

    READY = "ready"
    PROCESSING = "processing"
    REVIEW_PENDING = "review_pending"
    ANSWER_AVAILABLE = "answer_available"
    CLOSED = "closed"
    FAILED_CLOSED = "failed_closed"


class SseEventTypeV1(StrEnum):
    """Exact event types allowed at the participant stream boundary."""

    STATE_CHANGED = "state_changed"
    REVIEW_REQUIRED = "review_required"
    ANSWER_RELEASED = "answer_released"
    SESSION_CLOSED = "session_closed"
    FAILED_CLOSED = "failed_closed"
    HEARTBEAT = "heartbeat"


class SseEventV1(RuntimeContractModel):
    """Status-only event with an optional atomic, already released answer."""

    contract_version: ContractVersion
    event_id: NonBlankStr
    session_id: NonBlankStr
    sequence: int = Field(ge=0)
    event_type: SseEventTypeV1
    public_state: PublicSessionStateV1
    release_disposition: ReleaseDispositionV1
    released_turn: Turn | None

    @model_validator(mode="after")
    def validate_atomic_release(self) -> Self:
        is_answer = self.event_type is SseEventTypeV1.ANSWER_RELEASED
        if is_answer != (self.released_turn is not None):
            raise ValueError("released_turn exists exactly for answer_released")
        if is_answer:
            if self.release_disposition is not ReleaseDispositionV1.ALLOW:
                raise ValueError("answer_released requires allow")
            if self.public_state is not PublicSessionStateV1.ANSWER_AVAILABLE:
                raise ValueError("answer_released requires answer_available")
            if (
                self.released_turn is not None
                and self.released_turn.role != "assistant"
            ):
                raise ValueError("released_turn must have the assistant role")
        return self


class ParticipantSessionV1(RuntimeContractModel):
    """Participant projection containing only public state and released turns."""

    contract_version: ContractVersion
    session_id: NonBlankStr
    locale: NonBlankStr
    public_state: PublicSessionStateV1
    release_disposition: ReleaseDispositionV1
    released_turns: tuple[Turn, ...]

    @model_validator(mode="after")
    def validate_released_content(self) -> Self:
        if any(turn.role != "assistant" for turn in self.released_turns):
            raise ValueError("participant projection contains assistant turns only")
        turn_ids = tuple(turn.turn_id for turn in self.released_turns)
        if len(turn_ids) != len(set(turn_ids)):
            raise ValueError("released turns must have unique identities")
        return self


class CreateSessionRequestV1(RuntimeContractModel):
    """Create one explicitly synthetic, version-frozen research session."""

    contract_version: ContractVersion
    session_id: NonBlankStr
    scenario_id: NonBlankStr
    locale: NonBlankStr
    model_id: NonBlankStr
    policy_version: NonBlankStr
    plugin_profile_id: NonBlankStr
    evidence_registry_version: NonBlankStr
    adult_synthetic_role_play: Literal[True]


class SubmitTurnRequestV1(RuntimeContractModel):
    """One synthetic participant turn; HTTP supplies its idempotency key."""

    contract_version: ContractVersion
    request_id: NonBlankStr
    turn_id: NonBlankStr
    sequence: int = Field(ge=0)
    text: Annotated[str, Field(max_length=4000)]


class ReviewDecisionRequestV1(RuntimeContractModel):
    """One optimistic simulated-review decision."""

    contract_version: ContractVersion
    request_id: NonBlankStr
    decision: ReviewDecision
    expected_revision: int = Field(ge=0)
    resolved_at: AwareDatetime
    evidence_ids: NonEmptyStrings
    replacement_turn: Turn | None

    @model_validator(mode="after")
    def validate_replacement(self) -> Self:
        replacement_required = (
            self.decision is ReviewDecision.REPLACE_WITH_SAFE_TEMPLATE
        )
        if replacement_required != (self.replacement_turn is not None):
            raise ValueError("replacement turn exists exactly for replacement decision")
        return self


class CloseSessionRequestV1(RuntimeContractModel):
    """Close and evaluate one completely evidenced synthetic session."""

    contract_version: ContractVersion
    request_id: NonBlankStr
    trajectory_id: NonBlankStr
    evidence_ids: NonEmptyStrings


class PluginProfileUpdateRequestV1(RuntimeContractModel):
    """Admin request for a next-session-only preinstalled plugin profile."""

    contract_version: ContractVersion
    profile_version: NonBlankStr
    plugins: tuple[dict[str, JsonValue], ...]


class HealthViewV1(RuntimeContractModel):
    contract_version: ContractVersion
    status: Literal["ok", "not_ready"]
