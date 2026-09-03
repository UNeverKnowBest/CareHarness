import subprocess
import sys


def test_alembic_head_renders_postgresql_offline_sql() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head", "--sql"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    sql = result.stdout.casefold()
    assert "create table runtime_sessions" in sql
    assert "create table runtime_events" in sql
    assert "create table runtime_outbox" in sql
    assert "create table runtime_idempotency" in sql
    assert "create table plugin_profiles" in sql
    assert "create table review_queue" in sql
    assert "ix_review_queue_status_target" in sql
    assert "create table research_sessions" in sql
    assert "create table public_session_events" in sql
    assert "ix_research_sessions_retention" in sql
    assert "jsonb" in sql
