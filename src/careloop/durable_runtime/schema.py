"""SQLAlchemy metadata for the M14 PostgreSQL durable-runtime boundary."""

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB

metadata = MetaData()
json_document = JSON().with_variant(JSONB(), "postgresql")
outbox_identity = Integer().with_variant(BigInteger(), "postgresql")

runtime_sessions = Table(
    "runtime_sessions",
    metadata,
    Column("session_id", String(255), primary_key=True),
    Column("config", json_document, nullable=False),
    Column("current_state", String(64), nullable=False),
    Column("next_sequence", Integer, nullable=False),
    Column("retention_until", Date, nullable=True),
)

runtime_events = Table(
    "runtime_events",
    metadata,
    Column(
        "session_id",
        String(255),
        ForeignKey("runtime_sessions.session_id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("sequence", Integer, primary_key=True),
    Column("event_id", String(255), nullable=False),
    Column("payload", json_document, nullable=False),
    UniqueConstraint("event_id"),
)

runtime_outbox = Table(
    "runtime_outbox",
    metadata,
    Column("outbox_id", outbox_identity, primary_key=True, autoincrement=True),
    Column(
        "session_id",
        String(255),
        ForeignKey("runtime_sessions.session_id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("event_id", String(255), nullable=False),
    Column("sequence", Integer, nullable=False),
    Column("payload", json_document, nullable=False),
    Column("published", Boolean, nullable=False, default=False),
    UniqueConstraint("event_id"),
)
Index(
    "ix_runtime_outbox_unpublished",
    runtime_outbox.c.published,
    runtime_outbox.c.outbox_id,
)

runtime_idempotency = Table(
    "runtime_idempotency",
    metadata,
    Column(
        "session_id",
        String(255),
        ForeignKey("runtime_sessions.session_id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("request_id", String(255), primary_key=True),
    Column("request_hash", String(71), nullable=False),
    Column("result_payload", json_document, nullable=False),
)

plugin_profiles = Table(
    "plugin_profiles",
    metadata,
    Column("profile_id", String(255), primary_key=True),
    Column("profile_version", String(255), nullable=False),
    Column("payload", json_document, nullable=False),
)

review_queue = Table(
    "review_queue",
    metadata,
    Column("review_id", String(255), primary_key=True),
    Column(
        "session_id",
        String(255),
        ForeignKey("runtime_sessions.session_id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("request_id", String(255), nullable=False),
    Column("draft_id", String(255), nullable=False, unique=True),
    Column("status", String(32), nullable=False),
    Column("revision", Integer, nullable=False),
    Column("enqueued_at", DateTime(timezone=True), nullable=False),
    Column("review_target_at", DateTime(timezone=True), nullable=False),
    Column("payload", json_document, nullable=False),
    UniqueConstraint("session_id", "request_id"),
)
Index(
    "ix_review_queue_status_target",
    review_queue.c.status,
    review_queue.c.review_target_at,
)

research_sessions = Table(
    "research_sessions",
    metadata,
    Column(
        "session_id",
        String(255),
        ForeignKey("runtime_sessions.session_id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("owner_subject", String(255), nullable=False),
    Column("scenario_id", String(255), nullable=False),
    Column("locale", String(32), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("retention_until", Date, nullable=False),
    Column("request_payload", json_document, nullable=False),
    Column("participant_payload", json_document, nullable=False),
    Column("transcript_payload", json_document, nullable=False),
    Column("report_payload", json_document, nullable=True),
)
Index("ix_research_sessions_retention", research_sessions.c.retention_until)

public_session_events = Table(
    "public_session_events",
    metadata,
    Column(
        "session_id",
        String(255),
        ForeignKey("research_sessions.session_id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("sequence", Integer, primary_key=True),
    Column("event_id", String(255), nullable=False, unique=True),
    Column("payload", json_document, nullable=False),
)
