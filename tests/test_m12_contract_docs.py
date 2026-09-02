from pathlib import Path


def _normalized(path: str) -> str:
    return " ".join(Path(path).read_text(encoding="utf-8").split())


def test_m12_contract_is_frozen_in_normative_documents() -> None:
    spec = _normalized("SPEC.md")
    architecture = _normalized("ARCHITECTURE.md")
    plan = _normalized("PLAN.md")

    assert "Milestone 12 deterministic synthetic session-close contract" in spec
    assert "SyntheticSessionCloseCommand" in spec
    assert "SyntheticSessionSnapshot" in spec
    assert "evaluate in memory" in architecture
    assert "append CLOSE_SESSION before report release" in architecture
    assert "No Milestone 13 is approved" in plan


def test_m12_limits_are_recorded_in_runtime_safety_and_threat_documents() -> None:
    runtime = _normalized("docs/agent_runtime_contract.md")
    threat = _normalized("docs/threat_model.md")
    safety = _normalized("docs/safety_and_limitations.md")
    matrix = _normalized("docs/test_matrix.md")

    assert "FROZEN through Milestone 12" in runtime
    assert "Milestone 12 implemented controls" in threat
    assert "does not establish session quality" in safety
    assert "Milestone 12 synthetic session-close matrix" in matrix
