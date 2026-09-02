"""Create the M14 authoritative runtime, outbox, and plugin-profile tables."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260902_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "runtime_sessions",
        sa.Column("session_id", sa.String(length=255), nullable=False),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("current_state", sa.String(length=64), nullable=False),
        sa.Column("next_sequence", sa.Integer(), nullable=False),
        sa.Column("retention_until", sa.Date(), nullable=True),
        sa.PrimaryKeyConstraint("session_id"),
    )
    op.create_table(
        "plugin_profiles",
        sa.Column("profile_id", sa.String(length=255), nullable=False),
        sa.Column("profile_version", sa.String(length=255), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint("profile_id"),
    )
    op.create_table(
        "runtime_events",
        sa.Column("session_id", sa.String(length=255), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.String(length=255), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["runtime_sessions.session_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("session_id", "sequence"),
        sa.UniqueConstraint("event_id"),
    )
    op.create_table(
        "runtime_idempotency",
        sa.Column("session_id", sa.String(length=255), nullable=False),
        sa.Column("request_id", sa.String(length=255), nullable=False),
        sa.Column("request_hash", sa.String(length=71), nullable=False),
        sa.Column(
            "result_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["runtime_sessions.session_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("session_id", "request_id"),
    )
    op.create_table(
        "runtime_outbox",
        sa.Column("outbox_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.String(length=255), nullable=False),
        sa.Column("event_id", sa.String(length=255), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("published", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["runtime_sessions.session_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("outbox_id"),
        sa.UniqueConstraint("event_id"),
    )
    op.create_index(
        "ix_runtime_outbox_unpublished",
        "runtime_outbox",
        ["published", "outbox_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_runtime_outbox_unpublished", table_name="runtime_outbox")
    op.drop_table("runtime_outbox")
    op.drop_table("runtime_idempotency")
    op.drop_table("runtime_events")
    op.drop_table("plugin_profiles")
    op.drop_table("runtime_sessions")
