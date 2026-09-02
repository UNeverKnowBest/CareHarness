from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from careloop.agent_runtime import (
    PluginKind,
    RuntimeEvent,
    SessionConfig,
    SessionEvent,
    SessionState,
)
from careloop.durable_runtime import (
    DurableRuntimeConflict,
    PluginProfileEntryV1,
    PluginProfileV1,
    PostgresRuntimeStore,
    metadata,
    runtime_events,
    runtime_outbox,
    runtime_sessions,
)


def _config(profile: str = "profile-safe-default") -> SessionConfig:
    return SessionConfig(
        contract_version="v1",
        scenario_id="scenario-synthetic-001",
        locale="en",
        plugin_profile_id=profile,
    )


def _event(
    event_id: str,
    sequence: int,
    event: SessionEvent,
    before: SessionState,
    after: SessionState,
) -> RuntimeEvent:
    return RuntimeEvent(
        contract_version="v1",
        event_id=event_id,
        session_id="session-001",
        sequence=sequence,
        event=event,
        state_before=before,
        state_after=after,
        causation_id=f"cause:{event_id}",
        evidence_ids=(),
    )


def test_postgresql_schema_compiles_with_authoritative_constraints() -> None:
    dialect = postgresql.dialect()
    session_sql = str(CreateTable(runtime_sessions).compile(dialect=dialect))
    event_sql = str(CreateTable(runtime_events).compile(dialect=dialect))
    outbox_sql = str(CreateTable(runtime_outbox).compile(dialect=dialect))

    assert "JSONB" in session_sql
    assert "UNIQUE (event_id)" in event_sql
    assert "PRIMARY KEY (session_id, sequence)" in event_sql
    assert "published" in outbox_sql
    assert set(metadata.tables) >= {
        "runtime_sessions",
        "runtime_events",
        "runtime_outbox",
        "runtime_idempotency",
        "plugin_profiles",
    }


def test_store_persists_immutable_config_events_state_and_outbox(
    tmp_path: Path,
) -> None:
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'runtime.db'}")
    metadata.create_all(engine)
    store = PostgresRuntimeStore(engine)
    store.bind_session("session-001", _config())
    store.bind_session("session-001", _config())

    started = _event(
        "event-start",
        0,
        SessionEvent.START_SESSION,
        SessionState.CREATED,
        SessionState.ACTIVE,
    )
    submitted = _event(
        "event-submit",
        1,
        SessionEvent.SUBMIT_TURN,
        SessionState.ACTIVE,
        SessionState.DRAFTING,
    )
    store.append(started)
    store.append(submitted)

    recovered = PostgresRuntimeStore(engine)
    assert recovered.events_for("session-001") == (started, submitted)
    assert recovered.state_for("session-001") is SessionState.DRAFTING
    assert recovered.next_sequence("session-001") == 2
    assert tuple(item.event_id for item in recovered.pending_outbox(10)) == (
        "event-start",
        "event-submit",
    )

    with pytest.raises(DurableRuntimeConflict, match="immutable"):
        store.bind_session("session-001", _config("profile-other"))


def test_store_rejects_sequence_conflict_and_immutable_idempotency(
    tmp_path: Path,
) -> None:
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'runtime.db'}")
    metadata.create_all(engine)
    store = PostgresRuntimeStore(engine)
    store.bind_session("session-001", _config())
    store.append(
        _event(
            "event-start",
            0,
            SessionEvent.START_SESSION,
            SessionState.CREATED,
            SessionState.ACTIVE,
        )
    )

    with pytest.raises(DurableRuntimeConflict):
        store.append(
            _event(
                "event-skip",
                2,
                SessionEvent.SUBMIT_TURN,
                SessionState.ACTIVE,
                SessionState.DRAFTING,
            )
        )

    store.record_idempotency(
        session_id="session-001",
        request_id="request-001",
        request_hash="sha256:" + "a" * 64,
        result_payload={"status": "released"},
    )
    store.record_idempotency(
        session_id="session-001",
        request_id="request-001",
        request_hash="sha256:" + "a" * 64,
        result_payload={"status": "released"},
    )
    assert store.idempotency_result("session-001", "request-001") == {
        "status": "released"
    }

    with pytest.raises(DurableRuntimeConflict, match="idempotency"):
        store.record_idempotency(
            session_id="session-001",
            request_id="request-001",
            request_hash="sha256:" + "b" * 64,
            result_payload={"status": "different"},
        )


def test_store_persists_immutable_plugin_profile_snapshot(tmp_path: Path) -> None:
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'runtime.db'}")
    metadata.create_all(engine)
    store = PostgresRuntimeStore(engine)
    profile = PluginProfileV1(
        contract_version="v1",
        profile_id="profile-safe-default",
        profile_version="1",
        plugins=tuple(
            PluginProfileEntryV1(
                contract_version="v1",
                plugin_id=f"plugin-{kind.value}",
                plugin_version="1.0.0",
                kind=kind,
                enabled=True,
                locked=True,
                configuration={},
            )
            for kind in (
                PluginKind.MODEL_PROVIDER,
                PluginKind.INPUT_SAFETY_DETECTOR,
                PluginKind.OUTPUT_GUARD,
                PluginKind.RESOURCE_CATALOG,
            )
        ),
    )

    store.save_plugin_profile(profile)
    store.save_plugin_profile(profile)
    assert store.load_plugin_profile(profile.profile_id) == profile

    changed = profile.model_copy(update={"profile_version": "2"})
    with pytest.raises(DurableRuntimeConflict, match="immutable"):
        store.save_plugin_profile(changed)
