"""Transactional SQLAlchemy storage for append-only runtime evidence."""

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import Engine, create_engine, insert, select, update
from sqlalchemy.exc import IntegrityError

from careloop.agent_runtime import (
    ReviewDecision,
    RuntimeEvent,
    SessionConfig,
    SessionEvent,
    SessionState,
)
from careloop.durable_runtime.contracts import (
    PluginProfileV1,
    RuntimeOutboxRecord,
)
from careloop.durable_runtime.schema import (
    plugin_profiles,
    review_queue,
    runtime_events,
    runtime_idempotency,
    runtime_outbox,
    runtime_sessions,
)
from careloop.supervision.contracts import (
    ReviewQueueAuditV1,
    ReviewQueueItemV1,
    ReviewQueueStatus,
    require_aware,
)


class DurableRuntimeConflict(ValueError):
    """Raised when durable state would be mutated or appended inconsistently."""


def create_postgres_engine(database_url: str) -> Engine:
    """Create the production engine while rejecting non-PostgreSQL URLs."""
    if not database_url.startswith(("postgresql://", "postgresql+psycopg://")):
        raise ValueError("database_url must use PostgreSQL with psycopg")
    normalized = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return create_engine(normalized, pool_pre_ping=True)


class PostgresRuntimeStore:
    """Authoritative session/event store; Redis is deliberately not consulted."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def bind_session(self, session_id: str, config: SessionConfig) -> None:
        if not session_id.strip():
            raise ValueError("session_id must not be empty or whitespace")
        snapshot = SessionConfig.model_validate(config.model_dump())
        payload = snapshot.model_dump(mode="json")
        try:
            with self._engine.begin() as connection:
                row = (
                    connection.execute(
                        select(runtime_sessions.c.config)
                        .where(runtime_sessions.c.session_id == session_id)
                        .with_for_update()
                    )
                    .mappings()
                    .first()
                )
                if row is not None:
                    if SessionConfig.model_validate(row["config"]) != snapshot:
                        raise DurableRuntimeConflict(
                            f"session configuration is immutable for {session_id!r}"
                        )
                    return
                connection.execute(
                    insert(runtime_sessions).values(
                        session_id=session_id,
                        config=payload,
                        current_state=SessionState.CREATED.value,
                        next_sequence=0,
                    )
                )
        except IntegrityError as error:
            raise DurableRuntimeConflict(
                f"session bind conflicted for {session_id!r}"
            ) from error

    def append(self, event: RuntimeEvent) -> None:
        snapshot = RuntimeEvent.model_validate(event.model_dump())
        payload = snapshot.model_dump(mode="json")
        try:
            with self._engine.begin() as connection:
                session = (
                    connection.execute(
                        select(
                            runtime_sessions.c.current_state,
                            runtime_sessions.c.next_sequence,
                        )
                        .where(runtime_sessions.c.session_id == snapshot.session_id)
                        .with_for_update()
                    )
                    .mappings()
                    .first()
                )
                if session is None:
                    raise DurableRuntimeConflict(
                        f"unknown session: {snapshot.session_id!r}"
                    )
                expected_sequence = int(session["next_sequence"])
                expected_state = SessionState(str(session["current_state"]))
                if snapshot.sequence != expected_sequence:
                    raise DurableRuntimeConflict(
                        f"sequence must be contiguous: expected {expected_sequence}"
                    )
                if snapshot.state_before is not expected_state:
                    raise DurableRuntimeConflict(
                        f"state_before must equal last state: {expected_state.value}"
                    )
                connection.execute(
                    insert(runtime_events).values(
                        session_id=snapshot.session_id,
                        sequence=snapshot.sequence,
                        event_id=snapshot.event_id,
                        payload=payload,
                    )
                )
                connection.execute(
                    insert(runtime_outbox).values(
                        session_id=snapshot.session_id,
                        event_id=snapshot.event_id,
                        sequence=snapshot.sequence,
                        payload=payload,
                        published=False,
                    )
                )
                updated = connection.execute(
                    update(runtime_sessions)
                    .where(
                        runtime_sessions.c.session_id == snapshot.session_id,
                        runtime_sessions.c.next_sequence == expected_sequence,
                    )
                    .values(
                        current_state=snapshot.state_after.value,
                        next_sequence=expected_sequence + 1,
                    )
                )
                if updated.rowcount != 1:
                    raise DurableRuntimeConflict("concurrent session update detected")
        except IntegrityError as error:
            raise DurableRuntimeConflict("duplicate runtime event identity") from error

    def events_for(self, session_id: str) -> tuple[RuntimeEvent, ...]:
        self._require_session(session_id)
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(runtime_events.c.payload)
                .where(runtime_events.c.session_id == session_id)
                .order_by(runtime_events.c.sequence)
            ).mappings()
            return tuple(RuntimeEvent.model_validate(row["payload"]) for row in rows)

    def state_for(self, session_id: str) -> SessionState:
        row = self._require_session(session_id)
        return SessionState(str(row["current_state"]))

    def next_sequence(self, session_id: str) -> int:
        row = self._require_session(session_id)
        return int(row["next_sequence"])

    def pending_outbox(self, limit: int) -> tuple[RuntimeOutboxRecord, ...]:
        if limit < 1:
            raise ValueError("limit must be positive")
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(runtime_outbox)
                .where(runtime_outbox.c.published.is_(False))
                .order_by(runtime_outbox.c.outbox_id)
                .limit(limit)
            ).mappings()
            return tuple(
                RuntimeOutboxRecord(
                    contract_version="v1",
                    outbox_id=int(row["outbox_id"]),
                    session_id=str(row["session_id"]),
                    event_id=str(row["event_id"]),
                    sequence=int(row["sequence"]),
                    payload=dict(row["payload"]),
                )
                for row in rows
            )

    def mark_outbox_published(self, outbox_id: int) -> None:
        with self._engine.begin() as connection:
            result = connection.execute(
                update(runtime_outbox)
                .where(
                    runtime_outbox.c.outbox_id == outbox_id,
                    runtime_outbox.c.published.is_(False),
                )
                .values(published=True)
            )
            if result.rowcount != 1:
                raise DurableRuntimeConflict(
                    f"unknown or already published outbox_id: {outbox_id}"
                )

    def record_idempotency(
        self,
        *,
        session_id: str,
        request_id: str,
        request_hash: str,
        result_payload: Mapping[str, Any],
    ) -> None:
        if not request_id.strip() or not request_hash.strip():
            raise ValueError("request_id and request_hash must not be blank")
        with self._engine.begin() as connection:
            existing = (
                connection.execute(
                    select(
                        runtime_idempotency.c.request_hash,
                        runtime_idempotency.c.result_payload,
                    ).where(
                        runtime_idempotency.c.session_id == session_id,
                        runtime_idempotency.c.request_id == request_id,
                    )
                )
                .mappings()
                .first()
            )
            candidate = dict(result_payload)
            if existing is not None:
                if (
                    existing["request_hash"] != request_hash
                    or existing["result_payload"] != candidate
                ):
                    raise DurableRuntimeConflict("idempotency record is immutable")
                return
            connection.execute(
                insert(runtime_idempotency).values(
                    session_id=session_id,
                    request_id=request_id,
                    request_hash=request_hash,
                    result_payload=candidate,
                )
            )

    def idempotency_result(
        self, session_id: str, request_id: str
    ) -> dict[str, Any] | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(runtime_idempotency.c.result_payload).where(
                        runtime_idempotency.c.session_id == session_id,
                        runtime_idempotency.c.request_id == request_id,
                    )
                )
                .mappings()
                .first()
            )
            return None if row is None else dict(row["result_payload"])

    def save_plugin_profile(self, profile: PluginProfileV1) -> None:
        snapshot = PluginProfileV1.model_validate(profile.model_dump())
        payload = snapshot.model_dump(mode="json")
        with self._engine.begin() as connection:
            existing = (
                connection.execute(
                    select(plugin_profiles.c.payload).where(
                        plugin_profiles.c.profile_id == snapshot.profile_id
                    )
                )
                .mappings()
                .first()
            )
            if existing is not None:
                if PluginProfileV1.model_validate(existing["payload"]) != snapshot:
                    raise DurableRuntimeConflict("plugin profile is immutable")
                return
            connection.execute(
                insert(plugin_profiles).values(
                    profile_id=snapshot.profile_id,
                    profile_version=snapshot.profile_version,
                    payload=payload,
                )
            )

    def load_plugin_profile(self, profile_id: str) -> PluginProfileV1:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(plugin_profiles.c.payload).where(
                        plugin_profiles.c.profile_id == profile_id
                    )
                )
                .mappings()
                .first()
            )
            if row is None:
                raise DurableRuntimeConflict(f"unknown plugin profile: {profile_id!r}")
            return PluginProfileV1.model_validate(row["payload"])

    def enqueue_review(self, item: ReviewQueueItemV1) -> ReviewQueueItemV1:
        """Persist one immutable pending draft snapshot for simulated review."""
        snapshot = ReviewQueueItemV1.model_validate(item.model_dump())
        if snapshot.status is not ReviewQueueStatus.PENDING:
            raise ValueError("new review queue item must be pending")
        payload = snapshot.model_dump(mode="json")
        try:
            with self._engine.begin() as connection:
                existing = (
                    connection.execute(
                        select(review_queue.c.payload)
                        .where(review_queue.c.review_id == snapshot.review_id)
                        .with_for_update()
                    )
                    .mappings()
                    .first()
                )
                if existing is not None:
                    stored = ReviewQueueItemV1.model_validate(existing["payload"])
                    if stored != snapshot:
                        raise DurableRuntimeConflict("review queue item is immutable")
                    return stored
                connection.execute(
                    insert(review_queue).values(
                        review_id=snapshot.review_id,
                        session_id=snapshot.session_id,
                        request_id=snapshot.request_id,
                        draft_id=snapshot.draft.draft_id,
                        status=snapshot.status.value,
                        revision=snapshot.revision,
                        enqueued_at=snapshot.enqueued_at,
                        review_target_at=snapshot.review_target_at,
                        payload=payload,
                    )
                )
        except IntegrityError as error:
            raise DurableRuntimeConflict("duplicate review queue identity") from error
        return ReviewQueueItemV1.model_validate(payload)

    def review_item(self, review_id: str) -> ReviewQueueItemV1:
        """Load the authoritative reviewer-only snapshot."""
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(review_queue.c.payload).where(
                        review_queue.c.review_id == review_id
                    )
                )
                .mappings()
                .first()
            )
        if row is None:
            raise DurableRuntimeConflict(f"unknown review item: {review_id!r}")
        return ReviewQueueItemV1.model_validate(row["payload"])

    def claim_review(
        self,
        review_id: str,
        *,
        reviewer_id: str,
        expected_revision: int,
        claimed_at: datetime,
    ) -> ReviewQueueItemV1:
        """Claim a pending item using a caller-supplied optimistic revision."""
        if not reviewer_id.startswith("synthetic-reviewer:"):
            raise ValueError("reviewer_id must identify a synthetic-reviewer")
        require_aware(claimed_at, field_name="claimed_at")
        with self._engine.begin() as connection:
            current = self._locked_review(connection, review_id)
            if (
                current.status is not ReviewQueueStatus.PENDING
                or current.revision != expected_revision
            ):
                raise DurableRuntimeConflict("concurrent review claim detected")
            if claimed_at < current.enqueued_at:
                raise ValueError("claimed_at must not precede enqueued_at")
            claimed = current.model_copy(
                update={
                    "status": ReviewQueueStatus.CLAIMED,
                    "revision": current.revision + 1,
                    "claimed_by": reviewer_id,
                    "claimed_at": claimed_at,
                }
            )
            claimed = ReviewQueueItemV1.model_validate(claimed.model_dump())
            changed = connection.execute(
                update(review_queue)
                .where(
                    review_queue.c.review_id == review_id,
                    review_queue.c.status == ReviewQueueStatus.PENDING.value,
                    review_queue.c.revision == expected_revision,
                )
                .values(
                    status=claimed.status.value,
                    revision=claimed.revision,
                    payload=claimed.model_dump(mode="json"),
                )
            )
            if changed.rowcount != 1:
                raise DurableRuntimeConflict("concurrent review claim detected")
            return claimed

    def resolve_review(
        self,
        review_id: str,
        *,
        reviewer_id: str,
        expected_revision: int,
        decision: ReviewDecision,
        resolved_at: datetime,
        evidence_ids: Sequence[str],
    ) -> ReviewQueueItemV1:
        """Record one typed simulated-review decision with optimistic concurrency."""
        if not reviewer_id.startswith("synthetic-reviewer:"):
            raise ValueError("reviewer_id must identify a synthetic-reviewer")
        require_aware(resolved_at, field_name="resolved_at")
        if not evidence_ids or any(not item.strip() for item in evidence_ids):
            raise ValueError("resolution evidence_ids must be non-empty and non-blank")
        with self._engine.begin() as connection:
            current = self._locked_review(connection, review_id)
            if (
                current.status is not ReviewQueueStatus.CLAIMED
                or current.revision != expected_revision
                or current.claimed_by != reviewer_id
            ):
                raise DurableRuntimeConflict("concurrent review resolution detected")
            if current.claimed_at is None or resolved_at < current.claimed_at:
                raise ValueError("resolved_at must not precede claimed_at")
            combined_evidence = current.evidence_ids + tuple(evidence_ids)
            if len(combined_evidence) != len(set(combined_evidence)):
                raise ValueError("review evidence_ids must remain unique")
            resolved = current.model_copy(
                update={
                    "status": ReviewQueueStatus.RESOLVED,
                    "revision": current.revision + 1,
                    "resolved_at": resolved_at,
                    "decision": decision,
                    "evidence_ids": combined_evidence,
                }
            )
            resolved = ReviewQueueItemV1.model_validate(resolved.model_dump())
            changed = connection.execute(
                update(review_queue)
                .where(
                    review_queue.c.review_id == review_id,
                    review_queue.c.status == ReviewQueueStatus.CLAIMED.value,
                    review_queue.c.revision == expected_revision,
                )
                .values(
                    status=resolved.status.value,
                    revision=resolved.revision,
                    payload=resolved.model_dump(mode="json"),
                )
            )
            if changed.rowcount != 1:
                raise DurableRuntimeConflict("concurrent review resolution detected")
            return resolved

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
    ) -> ReviewQueueItemV1:
        """Atomically append a review event and advance its claimed queue row."""
        snapshot = RuntimeEvent.model_validate(event.model_dump())
        if snapshot.event not in {
            SessionEvent.REVIEW_APPROVED,
            SessionEvent.REVIEW_REPLACED,
            SessionEvent.REVIEW_HANDOFF,
            SessionEvent.REVIEW_REJECTED,
        }:
            raise ValueError("event must be a typed review resolution")
        expected_event = {
            ReviewDecision.APPROVE: SessionEvent.REVIEW_APPROVED,
            ReviewDecision.REPLACE_WITH_SAFE_TEMPLATE: SessionEvent.REVIEW_REPLACED,
            ReviewDecision.HANDOFF: SessionEvent.REVIEW_HANDOFF,
            ReviewDecision.REJECT: SessionEvent.REVIEW_REJECTED,
        }[decision]
        if snapshot.event is not expected_event:
            raise ValueError("review decision does not match runtime event")
        if not reviewer_id.startswith("synthetic-reviewer:"):
            raise ValueError("reviewer_id must identify a synthetic-reviewer")
        require_aware(resolved_at, field_name="resolved_at")
        if not evidence_ids or any(not item.strip() for item in evidence_ids):
            raise ValueError("resolution evidence_ids must be non-empty and non-blank")
        try:
            with self._engine.begin() as connection:
                current = self._locked_review(connection, review_id)
                if (
                    current.status is not ReviewQueueStatus.CLAIMED
                    or current.revision != expected_revision
                    or current.claimed_by != reviewer_id
                ):
                    raise DurableRuntimeConflict(
                        "concurrent review resolution detected"
                    )
                if current.claimed_at is None or resolved_at < current.claimed_at:
                    raise ValueError("resolved_at must not precede claimed_at")
                if current.session_id != snapshot.session_id:
                    raise ValueError("review event session does not match queue item")
                if current.draft.draft_id not in snapshot.evidence_ids:
                    raise ValueError("review event does not cite the queued draft")

                session = (
                    connection.execute(
                        select(
                            runtime_sessions.c.current_state,
                            runtime_sessions.c.next_sequence,
                        )
                        .where(runtime_sessions.c.session_id == snapshot.session_id)
                        .with_for_update()
                    )
                    .mappings()
                    .first()
                )
                if session is None:
                    raise DurableRuntimeConflict(
                        f"unknown session: {snapshot.session_id!r}"
                    )
                expected_sequence = int(session["next_sequence"])
                expected_state = SessionState(str(session["current_state"]))
                if snapshot.sequence != expected_sequence:
                    raise DurableRuntimeConflict(
                        f"sequence must be contiguous: expected {expected_sequence}"
                    )
                if snapshot.state_before is not expected_state:
                    raise DurableRuntimeConflict(
                        f"state_before must equal last state: {expected_state.value}"
                    )

                event_payload = snapshot.model_dump(mode="json")
                connection.execute(
                    insert(runtime_events).values(
                        session_id=snapshot.session_id,
                        sequence=snapshot.sequence,
                        event_id=snapshot.event_id,
                        payload=event_payload,
                    )
                )
                connection.execute(
                    insert(runtime_outbox).values(
                        session_id=snapshot.session_id,
                        event_id=snapshot.event_id,
                        sequence=snapshot.sequence,
                        payload=event_payload,
                        published=False,
                    )
                )
                session_changed = connection.execute(
                    update(runtime_sessions)
                    .where(
                        runtime_sessions.c.session_id == snapshot.session_id,
                        runtime_sessions.c.next_sequence == expected_sequence,
                    )
                    .values(
                        current_state=snapshot.state_after.value,
                        next_sequence=expected_sequence + 1,
                    )
                )
                if session_changed.rowcount != 1:
                    raise DurableRuntimeConflict("concurrent session update detected")

                combined_evidence = current.evidence_ids + tuple(evidence_ids)
                if len(combined_evidence) != len(set(combined_evidence)):
                    raise ValueError("review evidence_ids must remain unique")
                resolved = ReviewQueueItemV1.model_validate(
                    current.model_copy(
                        update={
                            "status": ReviewQueueStatus.RESOLVED,
                            "revision": current.revision + 1,
                            "resolved_at": resolved_at,
                            "decision": decision,
                            "evidence_ids": combined_evidence,
                        }
                    ).model_dump()
                )
                queue_changed = connection.execute(
                    update(review_queue)
                    .where(
                        review_queue.c.review_id == review_id,
                        review_queue.c.status == ReviewQueueStatus.CLAIMED.value,
                        review_queue.c.revision == expected_revision,
                    )
                    .values(
                        status=resolved.status.value,
                        revision=resolved.revision,
                        payload=resolved.model_dump(mode="json"),
                    )
                )
                if queue_changed.rowcount != 1:
                    raise DurableRuntimeConflict(
                        "concurrent review resolution detected"
                    )
                return resolved
        except IntegrityError as error:
            raise DurableRuntimeConflict(
                "duplicate or concurrent review resolution"
            ) from error

    def review_queue_audit(self, *, as_of: datetime) -> ReviewQueueAuditV1:
        """Derive descriptive queue evidence without wall-clock or scoring logic."""
        require_aware(as_of, field_name="as_of")
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(review_queue.c.payload).order_by(review_queue.c.review_id)
            ).mappings()
            items = tuple(
                ReviewQueueItemV1.model_validate(row["payload"]) for row in rows
            )
        pending = tuple(
            item for item in items if item.status is ReviewQueueStatus.PENDING
        )
        claimed = tuple(
            item for item in items if item.status is ReviewQueueStatus.CLAIMED
        )
        resolved = tuple(
            item for item in items if item.status is ReviewQueueStatus.RESOLVED
        )
        return ReviewQueueAuditV1(
            contract_version="v1",
            as_of=as_of,
            pending_count=len(pending),
            claimed_count=len(claimed),
            resolved_count=len(resolved),
            over_target_review_ids=tuple(
                item.review_id
                for item in pending + claimed
                if item.review_target_at < as_of
            ),
            within_target_resolution_ids=tuple(
                item.review_id
                for item in resolved
                if item.resolved_at is not None
                and item.resolved_at <= item.review_target_at
            ),
            after_target_resolution_ids=tuple(
                item.review_id
                for item in resolved
                if item.resolved_at is not None
                and item.resolved_at > item.review_target_at
            ),
        )

    @staticmethod
    def _locked_review(connection: Any, review_id: str) -> ReviewQueueItemV1:
        row = (
            connection.execute(
                select(review_queue.c.payload)
                .where(review_queue.c.review_id == review_id)
                .with_for_update()
            )
            .mappings()
            .first()
        )
        if row is None:
            raise DurableRuntimeConflict(f"unknown review item: {review_id!r}")
        return ReviewQueueItemV1.model_validate(row["payload"])

    def _require_session(self, session_id: str) -> dict[str, Any]:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(
                        runtime_sessions.c.current_state,
                        runtime_sessions.c.next_sequence,
                    ).where(runtime_sessions.c.session_id == session_id)
                )
                .mappings()
                .first()
            )
            if row is None:
                raise DurableRuntimeConflict(f"unknown session: {session_id!r}")
            return dict(row)
