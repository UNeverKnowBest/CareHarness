from pathlib import Path


def _normalized(path: str) -> str:
    return " ".join(Path(path).read_text(encoding="utf-8").split())


def test_m16_is_frozen_complete_and_m17_preserves_it() -> None:
    spec = _normalized("SPEC.md")
    architecture = _normalized("ARCHITECTURE.md")
    plan = _normalized("PLAN.md")
    status = _normalized("STATUS.md")

    assert "Milestone 16 research Web and service contract" in spec
    assert "ReleaseDispositionV1" in spec
    assert "Milestone 16 removable service and Web architecture" in architecture
    section = plan.split(
        "## Milestone 16 — FastAPI, Next.js, OIDC, reports, and Docker Compose"
    )[1]
    assert "Plan status: **COMPLETE**" in section
    assert "Milestone 17 complete" in status


def test_m16_limits_matrix_threats_and_delivery_status_are_recorded() -> None:
    safety = _normalized("docs/safety_and_limitations.md")
    matrix = _normalized("docs/test_matrix.md")
    threats = _normalized("docs/threat_model.md")
    readme = _normalized("README.md")

    assert "Milestone 16 Web/API matrix" in matrix
    assert "status-only SSE" in matrix
    assert "Milestone 16 implemented controls" in threats
    assert "not staffed care" in safety
    assert "Project status: Milestone 17 complete" in readme
    assert "Next.js" in readme
    assert "FastAPI" in readme
    assert "M16 remains independently removable" in readme
