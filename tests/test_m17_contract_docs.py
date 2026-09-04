from pathlib import Path

ROOT = Path(__file__).parents[1]


def _normalized(path: str) -> str:
    return " ".join((ROOT / path).read_text(encoding="utf-8").split())


def test_m17_is_frozen_complete_and_project_closing() -> None:
    spec = _normalized("SPEC.md")
    architecture = _normalized("ARCHITECTURE.md")
    plan = _normalized("PLAN.md")
    status = _normalized("STATUS.md")

    assert "Milestone 17 final evaluation and cloud delivery contract" in spec
    assert (
        "Milestone 17 removable evaluation and GCP template architecture"
        in architecture
    )
    section = plan.split(
        "## Milestone 17 — final evaluation, cloud template, and delivery"
    )[1]
    assert "Plan status: **COMPLETE**" in section
    assert "Current phase: Milestone 17 complete" in status
    assert "Next milestone: none" in status


def test_m17_limits_matrix_release_and_readme_guides_are_present() -> None:
    safety = _normalized("docs/safety_and_limitations.md").casefold()
    matrix = _normalized("docs/test_matrix.md")
    threats = _normalized("docs/threat_model.md")
    checklist = _normalized("docs/release_checklist.md").casefold()
    readme = _normalized("README.md").casefold()

    assert "Milestone 17 final-delivery matrix" in matrix
    assert "Milestone 17 deployment-template controls" in threats
    assert "does not establish cloud recovery" in safety
    assert "release checklist" in checklist
    assert "project status: milestone 17 complete" in readme
    assert "run the offline evaluator" in readme
    assert "run the local web demonstration" in readme
    assert "recommended demonstration video" in readme
    assert "do not enter real-person or protected health information" in readme
