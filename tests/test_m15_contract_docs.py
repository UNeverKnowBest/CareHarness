from pathlib import Path


def _normalized(path: str) -> str:
    return " ".join(Path(path).read_text(encoding="utf-8").split())


def test_m15_is_frozen_and_complete_in_normative_documents() -> None:
    spec = _normalized("SPEC.md")
    architecture = _normalized("ARCHITECTURE.md")
    plan = _normalized("PLAN.md")

    assert "Milestone 15 supervised safety orchestration contract" in spec
    assert "ReviewQueueItemV1" in spec
    assert "Milestone 15 supervised orchestration architecture" in architecture
    assert "append_review_resolution" in architecture
    section = plan.split(
        "## Milestone 15 — supervised safety orchestration and review queue"
    )[1]
    assert "Plan status: **COMPLETE**" in section


def test_m15_limits_matrix_and_delivery_status_are_recorded() -> None:
    safety = _normalized("docs/safety_and_limitations.md")
    matrix = _normalized("docs/test_matrix.md")
    readme = _normalized("README.md")

    assert "Milestone 15 supervised-orchestration matrix" in matrix
    assert "descriptive research target" in safety
    assert "not staffed care" in safety
    assert "M15 adds `SupervisedSyntheticTurn`" in readme
    assert "library-only composition" in readme
    assert "Project status: Milestone 17 complete" in readme
