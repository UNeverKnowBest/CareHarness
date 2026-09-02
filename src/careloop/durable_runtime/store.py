"""Transactional SQLAlchemy storage for append-only runtime evidence."""

from collections.abc import Mapping
from typing import Any

from sqlalchemy import Engine, create_engine, insert, select, update
from sqlalchemy.exc import IntegrityError

from careloop.agent_runtime import RuntimeEvent, SessionConfig, SessionState
from careloop.durable_runtime.contracts import (
    PluginProfileV1,
    RuntimeOutboxRecord,
)
from careloop.durable_runtime.schema import (
    plugin_profiles,
    runtime_events,
    runtime_idempotency,
    runtime_outbox,
    runtime_sessions,
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
