"""ARQ-compatible worker functions for retryable outbox delivery."""

from typing import Any

from careloop.durable_runtime.outbox import RedisOutboxPublisher


async def publish_runtime_outbox(context: dict[str, Any]) -> int:
    """Flush the injected publisher; ARQ retries exceptions without data loss."""
    publisher = context.get("runtime_outbox_publisher")
    if not isinstance(publisher, RedisOutboxPublisher):
        raise TypeError("runtime_outbox_publisher must be configured")
    return await publisher.flush()


class WorkerSettings:
    """Minimal ARQ discovery surface; deployment supplies startup resources."""

    functions = (publish_runtime_outbox,)
