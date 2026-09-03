"""Compose deployment resources for the M16 ARQ outbox worker."""

import os
from typing import Any, cast

from arq import cron
from arq.connections import RedisSettings

from careloop.durable_runtime import (
    PostgresRuntimeStore,
    RedisOutboxPublisher,
    create_postgres_engine,
    create_redis_client,
    publish_runtime_outbox,
)
from careloop.durable_runtime.outbox import RedisPublishPort


def _required_setting(name: str) -> str:
    value = os.getenv(name, "")
    if not value.strip():
        raise RuntimeError(f"{name} must be configured")
    return value


async def startup(context: dict[str, Any]) -> None:
    """Inject authoritative SQL and ephemeral Redis resources at worker startup."""
    engine = create_postgres_engine(_required_setting("CARELOOP_DATABASE_URL"))
    redis_client = create_redis_client(_required_setting("CARELOOP_REDIS_URL"))
    context["runtime_outbox_engine"] = engine
    context["runtime_outbox_redis"] = redis_client
    context["runtime_outbox_publisher"] = RedisOutboxPublisher(
        store=PostgresRuntimeStore(engine),
        redis_client=cast(RedisPublishPort, redis_client),
    )


async def shutdown(context: dict[str, Any]) -> None:
    """Close only the resources created by this deployment adapter."""
    redis_client = context.get("runtime_outbox_redis")
    if redis_client is not None:
        await redis_client.aclose()
    engine = context.get("runtime_outbox_engine")
    if engine is not None:
        engine.dispose()


class WorkerSettings:
    """ARQ discovery settings for retryable periodic outbox publication."""

    functions = (publish_runtime_outbox,)
    cron_jobs = (
        cron(
            "careloop.durable_runtime.worker.publish_runtime_outbox",
            second={0, 10, 20, 30, 40, 50},
        ),
    )
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(
        os.getenv("CARELOOP_REDIS_URL", "redis://localhost:6379/0")
    )
