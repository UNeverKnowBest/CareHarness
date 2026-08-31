import pytest

from careloop.agent_runtime import (
    InvalidSessionTransition,
    RuntimeEvent,
    SessionEvent,
    SessionState,
    transition_session,
)


@pytest.mark.parametrize(
    ("before", "event", "after"),
    [
        (SessionState.CREATED, SessionEvent.START_SESSION, SessionState.ACTIVE),
        (SessionState.ACTIVE, SessionEvent.SUBMIT_TURN, SessionState.DRAFTING),
        (
            SessionState.RESPONSE_RELEASED,
            SessionEvent.SUBMIT_TURN,
            SessionState.DRAFTING,
        ),
        (
            SessionState.DRAFTING,
            SessionEvent.DRAFT_GENERATED,
            SessionState.CHECKING_DRAFT,
        ),
        (
            SessionState.CHECKING_DRAFT,
            SessionEvent.DRAFT_APPROVED,
            SessionState.RESPONSE_RELEASED,
        ),
        (
            SessionState.CHECKING_DRAFT,
            SessionEvent.DRAFT_REWRITE_REQUESTED,
            SessionState.DRAFTING,
        ),
        (
            SessionState.CHECKING_DRAFT,
            SessionEvent.DRAFT_HELD_FOR_REVIEW,
            SessionState.AWAITING_HUMAN_REVIEW,
        ),
        (
            SessionState.AWAITING_HUMAN_REVIEW,
            SessionEvent.REVIEW_APPROVED,
            SessionState.RESPONSE_RELEASED,
        ),
        (
            SessionState.AWAITING_HUMAN_REVIEW,
            SessionEvent.REVIEW_REPLACED,
            SessionState.RESPONSE_RELEASED,
        ),
        (
            SessionState.AWAITING_HUMAN_REVIEW,
            SessionEvent.REVIEW_HANDOFF,
            SessionState.CLOSED,
        ),
        (SessionState.ACTIVE, SessionEvent.CLOSE_SESSION, SessionState.CLOSED),
        (
            SessionState.RESPONSE_RELEASED,
            SessionEvent.CLOSE_SESSION,
            SessionState.CLOSED,
        ),
    ],
)
def test_session_transition_table_is_explicit(
    before: SessionState,
    event: SessionEvent,
    after: SessionState,
) -> None:
    assert transition_session(before, event) is after


@pytest.mark.parametrize(
    "before",
    [
        SessionState.CREATED,
        SessionState.ACTIVE,
        SessionState.DRAFTING,
        SessionState.CHECKING_DRAFT,
        SessionState.AWAITING_HUMAN_REVIEW,
        SessionState.RESPONSE_RELEASED,
    ],
)
def test_any_nonterminal_runtime_failure_fails_closed(before: SessionState) -> None:
    assert (
        transition_session(before, SessionEvent.RUNTIME_FAILURE)
        is SessionState.FAILED_CLOSED
    )


@pytest.mark.parametrize(
    "terminal",
    [SessionState.CLOSED, SessionState.FAILED_CLOSED],
)
def test_terminal_states_cannot_be_reopened(terminal: SessionState) -> None:
    for event in SessionEvent:
        with pytest.raises(InvalidSessionTransition):
            transition_session(terminal, event)


def test_draft_cannot_be_released_without_checking() -> None:
    with pytest.raises(InvalidSessionTransition):
        transition_session(SessionState.DRAFTING, SessionEvent.DRAFT_APPROVED)


def test_human_review_cannot_be_bypassed_by_submitting_another_turn() -> None:
    with pytest.raises(InvalidSessionTransition):
        transition_session(
            SessionState.AWAITING_HUMAN_REVIEW,
            SessionEvent.SUBMIT_TURN,
        )


def test_runtime_event_records_one_validated_append_only_transition() -> None:
    event = RuntimeEvent(
        contract_version="v1",
        event_id="event-001",
        session_id="session-001",
        sequence=3,
        event=SessionEvent.DRAFT_GENERATED,
        state_before=SessionState.DRAFTING,
        state_after=SessionState.CHECKING_DRAFT,
        causation_id="request-001",
        evidence_ids=("draft-001",),
    )

    assert event.state_after is SessionState.CHECKING_DRAFT


def test_runtime_event_rejects_a_transition_projection_mismatch() -> None:
    with pytest.raises(ValueError, match="state_after"):
        RuntimeEvent(
            contract_version="v1",
            event_id="event-invalid",
            session_id="session-001",
            sequence=4,
            event=SessionEvent.DRAFT_APPROVED,
            state_before=SessionState.CHECKING_DRAFT,
            state_after=SessionState.AWAITING_HUMAN_REVIEW,
            causation_id="draft-001",
            evidence_ids=("finding-001",),
        )
