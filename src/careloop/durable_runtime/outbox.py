"""Best-effort Redis publication backed by the authoritative SQL outbox."""

import json
from typing import Protocol, cast

from redis.asyncio import Redis

from careloop.durable_runtime.contracts import RuntimeOutboxRecord


class RuntimeOutboxStorePort(Protocol):
    def pending_outbox(self, limit: int) -> tuple[RuntimeOutboxRecord, ...]: ...

    def mark_outbox_published(self, outbox_id: int) -> None: ...


class RedisPublishPort(Protocol):
    async def publish(self, channel: str, message: str) -> int: ...


def create_redis_client(redis_url: str) -> Redis:
    """Create a decoded async Redis client without performing a connection."""
    if not redis_url.startswith(("redis://", "rediss://")):
        raise ValueError("redis_url must use redis:// or rediss://")
    return cast(Redis, Redis.from_url(redis_url, decode_responses=True))


class RedisOutboxPublisher:
    """Publish committed event envelopes and mark only successful deliveries."""

    def __init__(
        self,
        *,
        store: RuntimeOutboxStorePort,
        redis_client: RedisPublishPort,
        channel_prefix: str = "careloop:session:",
    ) -> None:
        if not channel_prefix:
            raise ValueError("channel_prefix must not be empty")
        self._store = store
        self._redis = redis_client
        self._channel_prefix = channel_prefix

    async def flush(self, *, limit: int = 100) -> int:
        records = self._store.pending_outbox(limit)
        published = 0
        for record in records:
            message = json.dumps(
                record.payload,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            await self._redis.publish(
                f"{self._channel_prefix}{record.session_id}",
                message,
            )
            self._store.mark_outbox_published(record.outbox_id)
            published += 1
        return published
