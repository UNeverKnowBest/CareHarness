from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_ci_uses_lock_and_runs_required_gates_in_order() -> None:
    workflow = (ROOT / ".github" / "workflows" / "verify.yml").read_text(
        encoding="utf-8"
    )
    commands = (
        "uv sync --locked",
        "uv run --locked ruff format --check .",
        "uv run --locked ruff check .",
        "uv run --locked mypy src",
        "uv run --locked pytest -q",
        "uv run --locked careloop benchmark --manifest benchmarks/manifest.v1.json",
        "git diff --exit-code -- artifacts/raw artifacts/summary",
    )

    positions = tuple(workflow.index(command) for command in commands)
    assert positions == tuple(sorted(positions))


def test_readme_first_screen_states_product_boundary() -> None:
    first_screen = "\n".join(
        (ROOT / "README.md").read_text(encoding="utf-8").splitlines()[:30]
    ).casefold()

    for phrase in (
        "offline-first",
        "deterministic",
        "synthetic",
        "non-clinical",
        "not therapy",
        "not a medical device",
    ):
        assert phrase in first_screen


def test_readme_preserves_m15_history_and_records_current_m16_surface() -> None:
    readme = " ".join(
        (ROOT / "README.md").read_text(encoding="utf-8").split()
    ).casefold()

    for phrase in (
        "project status: milestone 16 complete",
        "postgresql/alembic adapter",
        "redis transactional-outbox publisher",
        "deepseek, vllm, and ollama",
        "runsyntheticturn",
        "resolvesyntheticreview",
        "closesyntheticsession",
        "in-memory trajectory evaluation",
        "append-only in-memory",
        "no installed plugin is enabled by default",
        "simulated review queue",
        "not staffed care",
        "offline cli remains the primary reproducible evaluation surface",
        "local research web/api demo",
        "read-only static html",
        "no server",
        "generated artifacts",
        "next milestone is m17",
    ):
        assert phrase in readme


def test_required_technical_documents_exist_without_handwritten_result_counts() -> None:
    threat_model = (ROOT / "docs" / "threat_model.md").read_text(encoding="utf-8")
    technical_report = (ROOT / "docs" / "technical_report.md").read_text(
        encoding="utf-8"
    )

    assert "untrusted" in threat_model.casefold()
    assert "fail closed" in threat_model.casefold()
    assert "artifacts/summary/benchmark.v1.summary.md" in technical_report
    assert "generated result counts are not copied into this document" in (
        technical_report.casefold()
    )
