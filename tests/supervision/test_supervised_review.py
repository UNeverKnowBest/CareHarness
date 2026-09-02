from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine

from careloop.agent_runtime import (
    ModelDraft,
    ReviewDecision,
    RuntimeEvent,
    SessionConfig,
    SessionEvent,
    SessionState,
)
from careloop.application.synthetic_review import SyntheticReviewCommand
from careloop.domain import Turn
from careloop.durable_runtime import (
    DurableRuntimeConflict,
    PostgresRuntimeStore,
    metadata,
)
from careloop.supervision import ReviewQueueItemV1, ReviewQueueStatus
from careloop.supervision.review_resolution import (
    QueuedSyntheticReviewCommand,
    ResolveQueuedSyntheticReview,
)

NOW = datetime(2026, 9, 2, 8, 0, tzinfo=UTC)


def _event(
    sequence: int,
    event: SessionEvent,
    before: SessionState,
    after: SessionState,
    evidence_ids: tuple[str, ...],
) -> RuntimeEvent:
    return RuntimeEvent(
        contract_version="v1",
        event_id=f"event-{sequence}",
        session_id="session-review",
        sequence=sequence,
        event=event,
        state_before=before,
        state_after=after,
        causation_id=f"cause-{sequence}",
        evidence_ids=evidence_ids,
    )


def _held_store(tmp_path: Path) -> tuple[PostgresRuntimeStore, ModelDraft]:
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'resolution.db'}")
    metadata.create_all(engine)
    store = PostgresRuntimeStore(engine)
    store.bind_session(
        "session-review",
        SessionConfig(
            contract_version="v1",
            scenario_id="scenario-review",
            locale="en",
            plugin_profile_id="profile-review",
        ),
    )
    draft = ModelDraft(
        contract_version="v1",
        request_id="model-request",
        draft_id="draft-held",
        text="[SYNTHETIC] Held draft.",
        provider_id="provider-test",
        model_name="model-test",
    )
    for event in (
        _event(
            0,
            SessionEvent.START_SESSION,
            SessionState.CREATED,
            SessionState.ACTIVE,
            ("scenario-review",),
        ),
        _event(
            1,
            SessionEvent.SUBMIT_TURN,
            SessionState.ACTIVE,
            SessionState.DRAFTING,
            ("turn-user",),
        ),
        _event(
            2,
            SessionEvent.DRAFT_GENERATED,
            SessionState.DRAFTING,
            SessionState.CHECKING_DRAFT,
            (draft.draft_id,),
        ),
        _event(
            3,
            SessionEvent.DRAFT_HELD_FOR_REVIEW,
            SessionState.CHECKING_DRAFT,
            SessionState.AWAITING_HUMAN_REVIEW,
            (draft.draft_id, "finding-held"),
        ),
    ):
        store.append(event)
    store.enqueue_review(
        ReviewQueueItemV1(
            contract_version="v1",
            review_id="review-atomic",
            session_id="session-review",
            request_id="turn-request",
            draft=draft,
            locale="en",
            status=ReviewQueueStatus.PENDING,
            revision=0,
            enqueued_at=NOW,
            review_target_at=NOW + timedelta(minutes=15),
            claimed_by=None,
            claimed_at=None,
            resolved_at=None,
            decision=None,
            evidence_ids=(draft.draft_id, "finding-held"),
        )
    )
    store.claim_review(
        "review-atomic",
        reviewer_id="synthetic-reviewer:alice",
        expected_revision=0,
        claimed_at=NOW + timedelta(minutes=1),
    )
    return store, draft


def _command(draft: ModelDraft, *, expected_revision: int = 1):
    release = Turn(
        turn_id="turn-assistant-reviewed",
        sequence=1,
        role="assistant",
        text=draft.text,
    )
    return QueuedSyntheticReviewCommand(
        contract_version="v1",
        review_id="review-atomic",
        reviewer_id="synthetic-reviewer:alice",
        expected_revision=expected_revision,
        resolved_at=NOW + timedelta(minutes=5),
        review=SyntheticReviewCommand(
            contract_version="v1",
            request_id="review-request",
            session_id="session-review",
            decision=ReviewDecision.APPROVE,
            reviewed_draft=draft,
            release_turn=release,
            evidence_ids=("review-evidence",),
        ),
    )


def test_review_decision_atomically_advances_ledger_outbox_and_queue(
    tmp_path: Path,
) -> None:
    store, draft = _held_store(tmp_path)

    result = ResolveQueuedSyntheticReview(store=store).execute(_command(draft))

    assert result.resolution.participant.released_turn is not None
    assert result.resolution.participant.released_turn.text == draft.text
    assert result.queue_item.status is ReviewQueueStatus.RESOLVED
    assert result.queue_item.revision == 2
    assert store.state_for("session-review") is SessionState.RESPONSE_RELEASED
    assert store.events_for("session-review")[-1].event is SessionEvent.REVIEW_APPROVED
    assert (
        store.pending_outbox(10)[-1].event_id
        == result.resolution.runtime_event.event_id
    )


def test_stale_review_revision_changes_neither_queue_nor_ledger(tmp_path: Path) -> None:
    store, draft = _held_store(tmp_path)
    before_events = store.events_for("session-review")
    before_item = store.review_item("review-atomic")

    with pytest.raises(DurableRuntimeConflict, match="concurrent"):
        ResolveQueuedSyntheticReview(store=store).execute(
            _command(draft, expected_revision=2)
        )

    assert store.events_for("session-review") == before_events
    assert store.review_item("review-atomic") == before_item
