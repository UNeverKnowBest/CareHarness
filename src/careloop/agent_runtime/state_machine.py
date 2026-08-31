"""Pure session transition table for the synthetic agent runtime."""

from enum import StrEnum
from typing import Annotated, Self

from pydantic import Field, model_validator

from careloop.agent_runtime.contracts import (
    ContractVersion,
    NonBlankStr,
    RuntimeContractModel,
    SessionState,
)


class SessionEvent(StrEnum):
    START_SESSION = "START_SESSION"
    SUBMIT_TURN = "SUBMIT_TURN"
    DRAFT_GENERATED = "DRAFT_GENERATED"
    DRAFT_APPROVED = "DRAFT_APPROVED"
    DRAFT_REWRITE_REQUESTED = "DRAFT_REWRITE_REQUESTED"
    DRAFT_HELD_FOR_REVIEW = "DRAFT_HELD_FOR_REVIEW"
    REVIEW_APPROVED = "REVIEW_APPROVED"
    REVIEW_REPLACED = "REVIEW_REPLACED"
    REVIEW_HANDOFF = "REVIEW_HANDOFF"
    REVIEW_REJECTED = "REVIEW_REJECTED"
    CLOSE_SESSION = "CLOSE_SESSION"
    RUNTIME_FAILURE = "RUNTIME_FAILURE"


class InvalidSessionTransition(ValueError):
    """Raised when an event attempts to bypass the frozen lifecycle."""


_TRANSITIONS: dict[tuple[SessionState, SessionEvent], SessionState] = {
    (SessionState.CREATED, SessionEvent.START_SESSION): SessionState.ACTIVE,
    (SessionState.ACTIVE, SessionEvent.SUBMIT_TURN): SessionState.DRAFTING,
    (
        SessionState.RESPONSE_RELEASED,
        SessionEvent.SUBMIT_TURN,
    ): SessionState.DRAFTING,
    (
        SessionState.DRAFTING,
        SessionEvent.DRAFT_GENERATED,
    ): SessionState.CHECKING_DRAFT,
    (
        SessionState.CHECKING_DRAFT,
        SessionEvent.DRAFT_APPROVED,
    ): SessionState.RESPONSE_RELEASED,
    (
        SessionState.CHECKING_DRAFT,
        SessionEvent.DRAFT_REWRITE_REQUESTED,
    ): SessionState.DRAFTING,
    (
        SessionState.CHECKING_DRAFT,
        SessionEvent.DRAFT_HELD_FOR_REVIEW,
    ): SessionState.AWAITING_HUMAN_REVIEW,
    (
        SessionState.AWAITING_HUMAN_REVIEW,
        SessionEvent.REVIEW_APPROVED,
    ): SessionState.RESPONSE_RELEASED,
    (
        SessionState.AWAITING_HUMAN_REVIEW,
        SessionEvent.REVIEW_REPLACED,
    ): SessionState.RESPONSE_RELEASED,
    (
        SessionState.AWAITING_HUMAN_REVIEW,
        SessionEvent.REVIEW_HANDOFF,
    ): SessionState.CLOSED,
    (
        SessionState.AWAITING_HUMAN_REVIEW,
        SessionEvent.REVIEW_REJECTED,
    ): SessionState.CLOSED,
    (SessionState.ACTIVE, SessionEvent.CLOSE_SESSION): SessionState.CLOSED,
    (
        SessionState.RESPONSE_RELEASED,
        SessionEvent.CLOSE_SESSION,
    ): SessionState.CLOSED,
}

_FAILURE_STATES = frozenset(
    {
        SessionState.CREATED,
        SessionState.ACTIVE,
        SessionState.DRAFTING,
        SessionState.CHECKING_DRAFT,
        SessionState.AWAITING_HUMAN_REVIEW,
        SessionState.RESPONSE_RELEASED,
    }
)


def transition_session(state: SessionState, event: SessionEvent) -> SessionState:
    """Return the next state or reject a lifecycle bypass."""
    if event is SessionEvent.RUNTIME_FAILURE and state in _FAILURE_STATES:
        return SessionState.FAILED_CLOSED
    try:
        return _TRANSITIONS[(state, event)]
    except KeyError as error:
        raise InvalidSessionTransition(
            f"event {event.value} is invalid from state {state.value}"
        ) from error


class RuntimeEvent(RuntimeContractModel):
    """One validated entry in the future append-only runtime ledger."""

    contract_version: ContractVersion
    event_id: NonBlankStr
    session_id: NonBlankStr
    sequence: Annotated[int, Field(ge=0)]
    event: SessionEvent
    state_before: SessionState
    state_after: SessionState
    causation_id: NonBlankStr
    evidence_ids: tuple[NonBlankStr, ...]

    @model_validator(mode="after")
    def validate_transition_projection(self) -> Self:
        expected = transition_session(self.state_before, self.event)
        if self.state_after is not expected:
            raise ValueError(
                f"state_after must equal the transition table result: {expected.value}"
            )
        return self
