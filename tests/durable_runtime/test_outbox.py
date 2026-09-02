import asyncio
from dataclasses import dataclass, field
from pathlib import Path

import pytest
from sqlalchemy import create_engine

from careloop.agent_runtime import (
    RuntimeEvent,
    SessionConfig,
    SessionEvent,
    SessionState,
)
from careloop.durable_runtime import (
    PostgresRuntimeStore,
    RedisOutboxPublisher,
    WorkerSettings,
    metadata,
    publish_runtime_outbox,
)


@dataclass
class FakeRedis:
    fail: bool = False
    published: list[tuple[str, str]] = field(default_factory=list)

    async def publish(self, channel: str, message: str) -> int:
        if self.fail:
            raise ConnectionError("redis unavailable")
        self.published.append((channel, message))
        return 1


def _store(tmp_path: Path) -> PostgresRuntimeStore:
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'runtime.db'}")
    metadata.create_all(engine)
    store = PostgresRuntimeStore(engine)
    store.bind_session(
        "session-001",
        SessionConfig(
            contract_version="v1",
            scenario_id="scenario-synthetic-001",
            locale="en",
            plugin_profile_id="profile-safe-default",
        ),
    )
    store.append(
        RuntimeEvent(
            contract_version="v1",
            event_id="event-start",
            session_id="session-001",
            sequence=0,
            event=SessionEvent.START_SESSION,
            state_before=SessionState.CREATED,
            state_after=SessionState.ACTIVE,
            causation_id="request-start",
            evidence_ids=(),
        )
    )
    return store


def test_redis_failure_leaves_authoritative_outbox_for_recovery(tmp_path: Path) -> None:
    store = _store(tmp_path)
    failing = RedisOutboxPublisher(store=store, redis_client=FakeRedis(fail=True))

    with pytest.raises(ConnectionError):
        asyncio.run(failing.flush(limit=10))
    assert len(store.pending_outbox(10)) == 1

    redis = FakeRedis()
    recovered = RedisOutboxPublisher(store=store, redis_client=redis)
    assert asyncio.run(recovered.flush(limit=10)) == 1
    assert store.pending_outbox(10) == ()
    assert redis.published[0][0] == "careloop:session:session-001"
    assert "event-start" in redis.published[0][1]


def test_arq_worker_function_uses_injected_publisher(tmp_path: Path) -> None:
    publisher = RedisOutboxPublisher(store=_store(tmp_path), redis_client=FakeRedis())

    result = asyncio.run(
        publish_runtime_outbox({"runtime_outbox_publisher": publisher})
    )

    assert result == 1
    assert publish_runtime_outbox in WorkerSettings.functions
