from pathlib import Path


def _normalized(path: str) -> str:
    return " ".join(Path(path).read_text(encoding="utf-8").split())


def test_m14_is_frozen_in_normative_documents() -> None:
    spec = _normalized("SPEC.md")
    architecture = _normalized("ARCHITECTURE.md")
    plan = _normalized("PLAN.md")

    assert "Milestone 14 durable runtime and model gateway contract" in spec
    assert "transactional outbox" in architecture
    assert "PostgresRuntimeStore" in architecture
    assert (
        "Plan status: **COMPLETE**"
        in plan.split(
            "## Milestone 14 — durable runtime, model gateway, and plugin profiles"
        )[1]
    )


def test_m14_limits_and_tests_are_recorded() -> None:
    safety = _normalized("docs/safety_and_limitations.md")
    matrix = _normalized("docs/test_matrix.md")
    readme = _normalized("README.md")

    assert "Milestone 14 durable-runtime matrix" in matrix
    assert "does not establish provider quality" in safety
    assert "M14 adds a PostgreSQL/Alembic adapter" in readme
    assert "no Web application or participant API" in readme
