from __future__ import annotations

from dataclasses import dataclass

import pytest
from pydantic import ValidationError

from careloop.agent_runtime import (
    ModelDraft,
    ReviewDecision,
    RuntimeEvent,
    SessionConfig,
    SessionEvent,
    SessionState,
)
from careloop.application.synthetic_review import (
    ParticipantReviewView,
    ResearchReviewResolutionView,
    ResolveSyntheticReview,
    ReviewIdempotencyConflict,
    ReviewLedgerUnavailable,
    ReviewStateConflict,
    SyntheticReviewCommand,
    SyntheticReviewFailureCode,
    SyntheticReviewStatus,
)
from careloop.domain import Turn
from careloop.runtime_storage import InMemoryRuntimeEventLedger


def _config() -> SessionConfig:
    return SessionConfig(
        contract_version="v1",
        scenario_id="scenario-synthetic-review",
        locale="en",
        plugin_profile_id="profile-synthetic-review",
    )


def _draft(draft_id: str = "draft-held") -> ModelDraft:
    return ModelDraft(
        contract_version="v1",
        request_id="model-request-held",
        draft_id=draft_id,
        text="[SYNTHETIC] Held draft text.",
        provider_id="provider-deterministic-test",
        model_name="deterministic-model-v1",
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
    session_id: str = "session-review-001",
) -> RuntimeEvent:
    return RuntimeEvent(
        contract_version="v1",
        event_id=event_id,
        session_id=session_id,
        sequence=sequence,
        event=event,
        state_before=before,
        state_after=after,
        causation_id=causation_id,
        evidence_ids=evidence_ids,
    )


def _held_ledger(draft: ModelDraft | None = None) -> InMemoryRuntimeEventLedger:
    draft = draft or _draft()
    ledger = InMemoryRuntimeEventLedger()
    ledger.bind_session("session-review-001", _config())
    events = (
        _event(
            event_id="event-start",
            sequence=0,
            event=SessionEvent.START_SESSION,
            before=SessionState.CREATED,
            after=SessionState.ACTIVE,
            causation_id="session-review-001:create",
            evidence_ids=("scenario-synthetic-review",),
        ),
        _event(
            event_id="event-submit",
            sequence=1,
            event=SessionEvent.SUBMIT_TURN,
            before=SessionState.ACTIVE,
            after=SessionState.DRAFTING,
            causation_id="turn-request",
            evidence_ids=("turn-user",),
        ),
        _event(
            event_id="event-draft",
            sequence=2,
            event=SessionEvent.DRAFT_GENERATED,
            before=SessionState.DRAFTING,
            after=SessionState.CHECKING_DRAFT,
            causation_id=draft.request_id,
            evidence_ids=(draft.draft_id,),
        ),
        _event(
            event_id="event-held",
            sequence=3,
            event=SessionEvent.DRAFT_HELD_FOR_REVIEW,
            before=SessionState.CHECKING_DRAFT,
            after=SessionState.AWAITING_HUMAN_REVIEW,
            causation_id=draft.draft_id,
            evidence_ids=(draft.draft_id, "finding-synthetic-review"),
        ),
    )
    for event in events:
        ledger.append(event)
    return ledger


def _release_turn(text: str = "[SYNTHETIC] Held draft text.") -> Turn:
    return Turn(
        turn_id="turn-review-assistant",
        sequence=1,
        role="assistant",
        text=text,
    )


def _command(
    decision: ReviewDecision = ReviewDecision.APPROVE,
    *,
    request_id: str = "review-request-001",
    draft: ModelDraft | None = None,
    release_turn: Turn | None = None,
) -> SyntheticReviewCommand:
    reviewed = draft or _draft()
    if release_turn is None and decision is ReviewDecision.APPROVE:
        release_turn = _release_turn(reviewed.text)
    elif release_turn is None and decision is ReviewDecision.REPLACE_WITH_SAFE_TEMPLATE:
        release_turn = _release_turn("[SYNTHETIC] Explicit replacement text.")
    return SyntheticReviewCommand(
        contract_version="v1",
        request_id=request_id,
        session_id="session-review-001",
        decision=decision,
        reviewed_draft=reviewed,
        release_turn=release_turn,
        evidence_ids=("review-evidence-synthetic",),
    )


def _resolver(
    ledger: InMemoryRuntimeEventLedger | FailingReviewLedger,
    *,
    held_draft: ModelDraft | None = None,
) -> ResolveSyntheticReview:
    return ResolveSyntheticReview(
        ledger=ledger,
        held_draft=held_draft or _draft(),
    )


@pytest.mark.parametrize(
    ("decision", "event", "status"),
    [
        (
            ReviewDecision.APPROVE,
            SessionEvent.REVIEW_APPROVED,
            SyntheticReviewStatus.APPROVED_RELEASED,
        ),
        (
            ReviewDecision.REPLACE_WITH_SAFE_TEMPLATE,
            SessionEvent.REVIEW_REPLACED,
            SyntheticReviewStatus.REPLACEMENT_RELEASED,
        ),
    ],
)
def test_approve_and_replace_append_before_atomic_release(
    decision: ReviewDecision,
    event: SessionEvent,
    status: SyntheticReviewStatus,
) -> None:
    ledger = _held_ledger()
    command = _command(decision)

    result = _resolver(ledger).execute(command)

    assert result.participant.status is status
    assert result.participant.state is SessionState.RESPONSE_RELEASED
    assert result.participant.released_turn == command.release_turn
    assert result.runtime_event.event is event
    assert ledger.events_for(command.session_id)[-1] == result.runtime_event


@pytest.mark.parametrize(
    ("decision", "event", "status"),
    [
        (
            ReviewDecision.HANDOFF,
            SessionEvent.REVIEW_HANDOFF,
            SyntheticReviewStatus.HANDED_OFF,
        ),
        (
            ReviewDecision.REJECT,
            SessionEvent.REVIEW_REJECTED,
            SyntheticReviewStatus.REJECTED,
        ),
    ],
)
def test_handoff_and_reject_close_without_release(
    decision: ReviewDecision,
    event: SessionEvent,
    status: SyntheticReviewStatus,
) -> None:
    ledger = _held_ledger()

    result = _resolver(ledger).execute(_command(decision))

    assert result.participant.status is status
    assert result.participant.state is SessionState.CLOSED
    assert result.participant.released_turn is None
    assert result.runtime_event.event is event


@pytest.mark.parametrize("invalid", ["state", "draft", "draft_content", "session"])
def test_stale_substituted_and_cross_session_reviews_reject_before_mutation(
    invalid: str,
) -> None:
    ledger = _held_ledger()
    command = _command()
    if invalid == "state":
        ledger.append(
            _event(
                event_id="event-runtime-failure",
                sequence=4,
                event=SessionEvent.RUNTIME_FAILURE,
                before=SessionState.AWAITING_HUMAN_REVIEW,
                after=SessionState.FAILED_CLOSED,
                causation_id="failure",
                evidence_ids=("synthetic-failure",),
            )
        )
    elif invalid == "draft":
        command = _command(draft=_draft("draft-substituted"))
    elif invalid == "draft_content":
        command = _command(
            draft=_draft().model_copy(
                update={"text": "[SYNTHETIC] Same ID, substituted text."}
            ),
            release_turn=_release_turn("[SYNTHETIC] Same ID, substituted text."),
        )
    else:
        command = command.model_copy(update={"session_id": "session-other"})
    before = ledger.events_for("session-review-001")

    with pytest.raises(ReviewStateConflict):
        _resolver(ledger).execute(command)

    assert ledger.events_for("session-review-001") == before


def test_command_decision_shapes_are_strict() -> None:
    with pytest.raises(ValidationError, match="unexpected"):
        SyntheticReviewCommand.model_validate(
            {**_command().model_dump(mode="json"), "unexpected": True}
        )
    with pytest.raises(ValidationError, match="exactly match"):
        _command(
            ReviewDecision.APPROVE,
            release_turn=_release_turn("[SYNTHETIC] Substituted approval text."),
        )
    with pytest.raises(ValidationError, match="release_turn"):
        SyntheticReviewCommand(
            **{
                **_command(ReviewDecision.HANDOFF).model_dump(),
                "release_turn": _release_turn(),
            }
        )
    with pytest.raises(ValidationError, match="assistant"):
        _command(
            ReviewDecision.REPLACE_WITH_SAFE_TEMPLATE,
            release_turn=Turn(
                turn_id="turn-user-invalid",
                sequence=1,
                role="user",
                text="[SYNTHETIC] Invalid replacement role.",
            ),
        )


def test_exact_retry_is_detached_and_conflicting_retry_rejects() -> None:
    ledger = _held_ledger()
    resolver = _resolver(ledger)
    command = _command()

    first = resolver.execute(command)
    second = resolver.execute(command)

    assert first == second
    assert len(ledger.events_for(command.session_id)) == 5
    assert first.participant.released_turn is not None
    first.participant.released_turn.text = "tampered outside resolver"
    assert resolver.execute(command).participant.released_turn == command.release_turn
    with pytest.raises(ReviewIdempotencyConflict):
        resolver.execute(
            command.model_copy(update={"evidence_ids": ("changed-evidence",)})
        )
    assert len(ledger.events_for(command.session_id)) == 5


@dataclass
class FailingReviewLedger:
    delegate: InMemoryRuntimeEventLedger
    persistent: bool

    def bind_session(self, session_id: str, config: SessionConfig) -> None:
        self.delegate.bind_session(session_id, config)

    def append(self, event: RuntimeEvent) -> None:
        if event.event in {
            SessionEvent.REVIEW_APPROVED,
            SessionEvent.REVIEW_REPLACED,
            SessionEvent.REVIEW_HANDOFF,
            SessionEvent.REVIEW_REJECTED,
        } or (self.persistent and event.event is SessionEvent.RUNTIME_FAILURE):
            raise RuntimeError("ledger secret must not escape")
        self.delegate.append(event)

    def events_for(self, session_id: str) -> tuple[RuntimeEvent, ...]:
        return self.delegate.events_for(session_id)

    def state_for(self, session_id: str) -> SessionState:
        return self.delegate.state_for(session_id)

    def next_sequence(self, session_id: str) -> int:
        return self.delegate.next_sequence(session_id)


def test_one_shot_review_append_failure_records_failed_closed_without_release() -> None:
    ledger = FailingReviewLedger(_held_ledger(), persistent=False)

    result = _resolver(ledger).execute(_command())

    assert result.failure_code is SyntheticReviewFailureCode.LEDGER_FAILURE
    assert result.participant.status is SyntheticReviewStatus.FAILED_CLOSED
    assert result.participant.state is SessionState.FAILED_CLOSED
    assert result.participant.released_turn is None
    assert result.runtime_event.event is SessionEvent.RUNTIME_FAILURE
    assert result.runtime_event.evidence_ids == ("synthetic_review:ledger_failure",)
    assert "secret" not in result.model_dump_json()


def test_persistent_review_ledger_failure_raises_without_release() -> None:
    ledger = FailingReviewLedger(_held_ledger(), persistent=True)

    with pytest.raises(ReviewLedgerUnavailable, match="no output was released"):
        _resolver(ledger).execute(_command())

    assert ledger.delegate.state_for("session-review-001") is (
        SessionState.AWAITING_HUMAN_REVIEW
    )
    assert len(ledger.delegate.events_for("session-review-001")) == 4


def test_participant_and_research_review_projections_are_isolated() -> None:
    assert set(ParticipantReviewView.model_fields) == {
        "contract_version",
        "request_id",
        "session_id",
        "status",
        "state",
        "released_turn",
    }
    assert set(ResearchReviewResolutionView.model_fields) == {
        "contract_version",
        "participant",
        "decision",
        "reviewed_draft",
        "runtime_event",
        "failure_code",
    }
    forbidden = {
        "decision",
        "reviewed_draft",
        "evidence_ids",
        "runtime_event",
        "failure_code",
        "chain_of_thought",
        "risk_score",
        "diagnosis",
        "clinical_disposition",
    }
    assert forbidden.isdisjoint(ParticipantReviewView.model_fields)
