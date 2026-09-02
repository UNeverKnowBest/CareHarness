from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine

from careloop.agent_runtime import ModelDraft, ReviewDecision
from careloop.durable_runtime import (
    DurableRuntimeConflict,
    PostgresRuntimeStore,
    metadata,
)
from careloop.supervision import ReviewQueueItemV1, ReviewQueueStatus

ENQUEUED = datetime(2026, 9, 2, 8, 0, tzinfo=UTC)


def _store(tmp_path: Path) -> PostgresRuntimeStore:
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'review.db'}")
    metadata.create_all(engine)
    return PostgresRuntimeStore(engine)


def _item(review_id: str = "review-001") -> ReviewQueueItemV1:
    return ReviewQueueItemV1(
        contract_version="v1",
        review_id=review_id,
        session_id=f"session-{review_id}",
        request_id=f"request-{review_id}",
        draft=ModelDraft(
            contract_version="v1",
            request_id=f"model-{review_id}",
            draft_id=f"draft-{review_id}",
            text="[SYNTHETIC] Reviewer-only quarantined draft.",
            provider_id="provider-test",
            model_name="model-test",
        ),
        locale="en",
        status=ReviewQueueStatus.PENDING,
        revision=0,
        enqueued_at=ENQUEUED,
        review_target_at=ENQUEUED + timedelta(minutes=15),
        claimed_by=None,
        claimed_at=None,
        resolved_at=None,
        decision=None,
        evidence_ids=("finding-output-policy",),
    )


def test_review_queue_claim_and_resolution_use_optimistic_concurrency(
    tmp_path: Path,
) -> None:
    store = _store(tmp_path)
    pending = _item()
    store.enqueue_review(pending)
    assert store.review_item(pending.review_id) == pending

    claimed = store.claim_review(
        pending.review_id,
        reviewer_id="synthetic-reviewer:alice",
        expected_revision=0,
        claimed_at=ENQUEUED + timedelta(minutes=2),
    )
    assert claimed.status is ReviewQueueStatus.CLAIMED
    assert claimed.revision == 1

    with pytest.raises(DurableRuntimeConflict, match="concurrent"):
        store.claim_review(
            pending.review_id,
            reviewer_id="synthetic-reviewer:bob",
            expected_revision=0,
            claimed_at=ENQUEUED + timedelta(minutes=3),
        )

    resolved = store.resolve_review(
        pending.review_id,
        reviewer_id="synthetic-reviewer:alice",
        expected_revision=1,
        decision=ReviewDecision.REJECT,
        resolved_at=ENQUEUED + timedelta(minutes=10),
        evidence_ids=("review-evidence-001",),
    )
    assert resolved.status is ReviewQueueStatus.RESOLVED
    assert resolved.revision == 2
    assert resolved.decision is ReviewDecision.REJECT

    with pytest.raises(DurableRuntimeConflict, match="concurrent"):
        store.resolve_review(
            pending.review_id,
            reviewer_id="synthetic-reviewer:alice",
            expected_revision=1,
            decision=ReviewDecision.APPROVE,
            resolved_at=ENQUEUED + timedelta(minutes=11),
            evidence_ids=("changed",),
        )


def test_review_queue_audit_is_derived_from_explicit_time_and_raw_rows(
    tmp_path: Path,
) -> None:
    store = _store(tmp_path)
    within = _item("within")
    late = _item("late")
    pending = _item("pending")
    for item in (within, late, pending):
        store.enqueue_review(item)
    for item, minutes in ((within, 10), (late, 20)):
        claimed = store.claim_review(
            item.review_id,
            reviewer_id=f"synthetic-reviewer:{item.review_id}",
            expected_revision=0,
            claimed_at=ENQUEUED + timedelta(minutes=1),
        )
        store.resolve_review(
            item.review_id,
            reviewer_id=claimed.claimed_by or "",
            expected_revision=1,
            decision=ReviewDecision.REJECT,
            resolved_at=ENQUEUED + timedelta(minutes=minutes),
            evidence_ids=(f"evidence-{item.review_id}",),
        )

    audit = store.review_queue_audit(as_of=ENQUEUED + timedelta(minutes=30))

    assert audit.pending_count == 1
    assert audit.claimed_count == 0
    assert audit.resolved_count == 2
    assert audit.over_target_review_ids == ("pending",)
    assert audit.within_target_resolution_ids == ("within",)
    assert audit.after_target_resolution_ids == ("late",)
    assert "score" not in audit.model_dump_json().casefold()


def test_review_queue_rejects_non_synthetic_reviewer_and_invalid_time_order(
    tmp_path: Path,
) -> None:
    store = _store(tmp_path)
    item = _item()
    store.enqueue_review(item)

    with pytest.raises(ValueError, match="synthetic-reviewer"):
        store.claim_review(
            item.review_id,
            reviewer_id="real-clinician",
            expected_revision=0,
            claimed_at=ENQUEUED,
        )
    with pytest.raises(ValueError, match="enqueued"):
        store.claim_review(
            item.review_id,
            reviewer_id="synthetic-reviewer:alice",
            expected_revision=0,
            claimed_at=ENQUEUED - timedelta(seconds=1),
        )
