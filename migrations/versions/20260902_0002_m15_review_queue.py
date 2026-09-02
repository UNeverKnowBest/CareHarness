"""Add the M15 simulated research-review queue."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260902_0002"
down_revision: str | None = "20260902_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "review_queue",
        sa.Column("review_id", sa.String(length=255), nullable=False),
        sa.Column("session_id", sa.String(length=255), nullable=False),
        sa.Column("request_id", sa.String(length=255), nullable=False),
        sa.Column("draft_id", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("enqueued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("review_target_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(
            ["session_id"], ["runtime_sessions.session_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("review_id"),
        sa.UniqueConstraint("draft_id"),
        sa.UniqueConstraint("session_id", "request_id"),
    )
    op.create_index(
        "ix_review_queue_status_target",
        "review_queue",
        ["status", "review_target_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_review_queue_status_target", table_name="review_queue")
    op.drop_table("review_queue")
