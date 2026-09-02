from pathlib import Path


def _normalized(path: str) -> str:
    return " ".join(Path(path).read_text(encoding="utf-8").split())


def test_m11_contract_is_frozen_in_normative_documents() -> None:
    spec = _normalized("SPEC.md")
    architecture = _normalized("ARCHITECTURE.md")
    plan = _normalized("PLAN.md")

    assert "Milestone 11 deterministic synthetic review-resolution contract" in spec
    assert "SyntheticReviewCommand" in spec
    assert "APPROVE" in spec
    assert "REPLACE_WITH_SAFE_TEMPLATE" in spec
    assert "append decision event" in architecture
    assert "No Milestone 12 is approved" in plan


def test_m11_limits_are_recorded_in_safety_and_threat_documents() -> None:
    runtime = _normalized("docs/agent_runtime_contract.md")
    threat = _normalized("docs/threat_model.md")
    safety = _normalized("docs/safety_and_limitations.md")
    matrix = _normalized("docs/test_matrix.md")

    assert "FROZEN through Milestone 11" in runtime
    assert "Milestone 11 implemented controls" in threat
    assert "does not contact a person" in safety
    assert "Milestone 11 synthetic review-resolution matrix" in matrix
