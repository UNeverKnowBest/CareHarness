"""Add M16 authoritative research-session and public-event projections."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260903_0003"
down_revision: str | None = "20260902_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "research_sessions",
        sa.Column("session_id", sa.String(length=255), nullable=False),
        sa.Column("owner_subject", sa.String(length=255), nullable=False),
        sa.Column("scenario_id", sa.String(length=255), nullable=False),
        sa.Column("locale", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("retention_until", sa.Date(), nullable=False),
        sa.Column(
            "request_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column(
            "participant_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "transcript_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "report_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.ForeignKeyConstraint(
            ["session_id"], ["runtime_sessions.session_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("session_id"),
    )
    op.create_index(
        "ix_research_sessions_retention",
        "research_sessions",
        ["retention_until"],
        unique=False,
    )
    op.create_table(
        "public_session_events",
        sa.Column("session_id", sa.String(length=255), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.String(length=255), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(
            ["session_id"], ["research_sessions.session_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("session_id", "sequence"),
        sa.UniqueConstraint("event_id"),
    )


def downgrade() -> None:
    op.drop_table("public_session_events")
    op.drop_index("ix_research_sessions_retention", table_name="research_sessions")
    op.drop_table("research_sessions")
