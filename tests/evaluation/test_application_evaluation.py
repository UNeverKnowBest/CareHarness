from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from careloop.application import EvaluateTrajectory, EvaluationError
from careloop.artifacts import build_frozen_trajectory_artifact
from careloop.domain import FinalAnswerView, Trajectory, Turn
from careloop.evaluation import FinalAnswerEvaluator
from careloop.evaluation.registry import load_evaluation_policy
from careloop.process import load_process_policy

ROOT = Path(__file__).parents[2]
TRAJECTORY_ROOT = ROOT / "benchmarks" / "trajectories"
MANIFEST_PATH = ROOT / "benchmarks" / "manifest.v1.json"
PROCESS_POLICY_PATH = ROOT / "policies" / "process.v1.json"
CRISIS_POLICY_PATH = ROOT / "policies" / "crisis.v1.json"
RESOURCE_POLICY_PATH = ROOT / "policies" / "resources.v1.json"
EVALUATION_POLICY_PATH = ROOT / "policies" / "evaluation.v1.json"

EXPECTED_RULE_IDS = (
    "session.collaborative_agenda_violation",
    "mi.autonomy_violation_after_decline",
    "cbt.permission_violation",
    "session.diagnosis_claim",
    "mi.agent_owned_action_plan",
    "cbt.multiple_agreed_skill_paths",
    "mi.invalid_process_transition",
    "safety.ambiguous_override_recorded",
    "safety.emergency_override_recorded",
    "safety.resource_locale_version_integrity",
)

PAIR_EXPECTATIONS = {
    "p1": ("session.collaborative_agenda_violation", "absent", "present"),
    "p2": ("mi.autonomy_violation_after_decline", "absent", "present"),
    "p3": ("cbt.permission_violation", "absent", "present"),
    "p4": ("session.diagnosis_claim", "absent", "present"),
    "p5": ("mi.agent_owned_action_plan", "absent", "present"),
    "p6": ("safety.ambiguous_override_recorded", "present", "absent"),
    "p7": ("safety.emergency_override_recorded", "present", "absent"),
    "p8": ("safety.resource_locale_version_integrity", "present", "absent"),
}


@pytest.fixture(scope="module")
def service() -> EvaluateTrajectory:
    return EvaluateTrajectory.from_paths(
        benchmark_manifest_path=MANIFEST_PATH,
        process_policy_path=PROCESS_POLICY_PATH,
        crisis_policy_path=CRISIS_POLICY_PATH,
        resource_policy_path=RESOURCE_POLICY_PATH,
        evaluation_policy_path=EVALUATION_POLICY_PATH,
    )


def _outcome(result: object, rule_id: str) -> str:
    findings = result.trajectory_findings  # type: ignore[attr-defined]
    return next(finding.outcome for finding in findings if finding.rule_id == rule_id)


def test_final_answer_evaluator_accepts_only_the_narrow_view() -> None:
    evaluator = FinalAnswerEvaluator(
        load_process_policy(PROCESS_POLICY_PATH),
        load_evaluation_policy(EVALUATION_POLICY_PATH),
    )
    view = FinalAnswerView(text="[SYNTHETIC] Final-only view.", turn_id="t-final")

    findings = evaluator.evaluate(view)

    assert tuple(finding.rule_id for finding in findings) == EXPECTED_RULE_IDS
    assert all(finding.turn_ids == ("t-final",) for finding in findings)
    with pytest.raises(TypeError, match="FinalAnswerView"):
        evaluator.evaluate(  # type: ignore[arg-type]
            Trajectory(
                trajectory_schema_version="v1",
                trajectory_id="wrong-boundary",
                turns=(Turn(turn_id="t0", sequence=0, role="assistant", text="x"),),
                process_markers=(),
                safety_events=(),
            )
        )


def test_evaluate_trajectory_builds_final_view_and_stable_ledgers(
    service: EvaluateTrajectory, tmp_path: Path
) -> None:
    output_path = tmp_path / "p1-bad.evaluation.json"

    first = service.run(TRAJECTORY_ROOT / "p1-bad.json", output_path=output_path)
    second = service.run(TRAJECTORY_ROOT / "p1-bad.json")

    assert first == second
    assert first.result_schema_version == "v1"
    assert first.case_id == "p1-bad"
    assert first.as_of == date(2026, 8, 29)
    assert first.final_answer.turn_id == "p1-t3"
    assert tuple(finding.rule_id for finding in first.final_answer_findings) == (
        EXPECTED_RULE_IDS
    )
    assert tuple(finding.rule_id for finding in first.trajectory_findings) == (
        EXPECTED_RULE_IDS
    )
    assert all(
        finding.outcome == "uncertain" for finding in first.final_answer_findings
    )
    assert output_path.read_bytes() == first.canonical_bytes()
    assert b"gold" not in output_path.read_bytes().lower()
    assert b"comparison" not in output_path.read_bytes().lower()


@pytest.mark.parametrize("pair", tuple(PAIR_EXPECTATIONS))
def test_all_pairs_localize_the_frozen_trajectory_difference(
    service: EvaluateTrajectory, pair: str
) -> None:
    rule_id, good_outcome, bad_outcome = PAIR_EXPECTATIONS[pair]

    good = service.run(TRAJECTORY_ROOT / f"{pair}-good.json")
    bad = service.run(TRAJECTORY_ROOT / f"{pair}-bad.json")

    assert _outcome(good, rule_id) == good_outcome
    assert _outcome(bad, rule_id) == bad_outcome
    assert good.final_answer == bad.final_answer
    assert good.final_answer_findings == bad.final_answer_findings
    evidence = next(
        finding for finding in bad.trajectory_findings if finding.rule_id == rule_id
    )
    assert evidence.turn_ids == (f"{pair}-t1",)
    bad.trajectory.validate_finding(evidence)


def test_resource_references_preserve_registered_synthetic_provenance(
    service: EvaluateTrajectory,
) -> None:
    result = service.run(TRAJECTORY_ROOT / "p8-bad.json")

    assert tuple(item.resource_id for item in result.resource_references) == (
        "synthetic-human-help-zz-other",
    )
    assert result.resource_references[0].registered is True
    assert result.resource_references[0].resource is not None
    assert (
        result.resource_references[0].resource.source_url.endswith(".invalid") is False
    )
    assert ".invalid/" in result.resource_references[0].resource.source_url


def test_missing_fixture_jurisdiction_is_uncertain_and_never_guessed(
    service: EvaluateTrajectory, tmp_path: Path
) -> None:
    original = service.run(TRAJECTORY_ROOT / "p8-good.json")
    turns = (
        original.trajectory.turns[0].model_copy(
            update={
                "text": (
                    "[SYNTHETIC SAFETY SIGNAL: CURRENT PREPARATION] "
                    "No jurisdiction is supplied for this frozen artifact."
                )
            }
        ),
    ) + original.trajectory.turns[1:]
    trajectory = original.trajectory.model_copy(update={"turns": turns})
    artifact = build_frozen_trajectory_artifact(
        case_id="synthetic-missing-jurisdiction", trajectory=trajectory
    )
    path = tmp_path / "missing-jurisdiction.json"
    path.write_bytes(artifact.stored_bytes())

    result = service.run(path)

    assert _outcome(result, "safety.resource_locale_version_integrity") == "uncertain"


def test_override_observation_requires_event_source_evidence(
    service: EvaluateTrajectory, tmp_path: Path
) -> None:
    original = service.run(TRAJECTORY_ROOT / "p7-good.json")
    event = original.trajectory.safety_events[0].model_copy(
        update={"source_ids": ("synthetic-unrelated-source",)}
    )
    trajectory = original.trajectory.model_copy(update={"safety_events": (event,)})
    artifact = build_frozen_trajectory_artifact(
        case_id="synthetic-unlinked-override", trajectory=trajectory
    )
    path = tmp_path / "unlinked-override.json"
    path.write_bytes(artifact.stored_bytes())

    result = service.run(path)

    assert _outcome(result, "safety.emergency_override_recorded") == "absent"


def test_evaluation_registry_rejects_unknown_version_source_and_signal(
    tmp_path: Path,
) -> None:
    raw = EVALUATION_POLICY_PATH.read_text(encoding="utf-8")
    unknown_version = tmp_path / "unknown-version.json"
    unknown_version.write_text(
        raw.replace('"policy_schema_version": "v1"', '"policy_schema_version": "v2"'),
        encoding="utf-8",
    )
    unknown_source = tmp_path / "unknown-source.json"
    unknown_source.write_text(
        raw.replace(
            '"source_ids": ["source-guide-m4-safety"]',
            '"source_ids": ["missing-source"]',
            1,
        ),
        encoding="utf-8",
    )
    unknown_signal = tmp_path / "unknown-signal.json"
    unknown_signal.write_text(
        raw.replace('"ambiguous_current"', '"missing-signal"', 1),
        encoding="utf-8",
    )

    with pytest.raises(ValidationError, match="policy_schema_version"):
        load_evaluation_policy(unknown_version)
    with pytest.raises(ValidationError, match="unknown source"):
        load_evaluation_policy(unknown_source)
    with pytest.raises(ValueError, match="unknown crisis signal"):
        EvaluateTrajectory.from_paths(
            benchmark_manifest_path=MANIFEST_PATH,
            process_policy_path=PROCESS_POLICY_PATH,
            crisis_policy_path=CRISIS_POLICY_PATH,
            resource_policy_path=RESOURCE_POLICY_PATH,
            evaluation_policy_path=unknown_signal,
        )


def test_trajectory_without_assistant_turn_fails_visibly(
    service: EvaluateTrajectory, tmp_path: Path
) -> None:
    trajectory = Trajectory(
        trajectory_schema_version="v1",
        trajectory_id="synthetic-no-assistant",
        turns=(
            Turn(
                turn_id="t0",
                sequence=0,
                role="user",
                text="[SYNTHETIC] User-only frozen trajectory.",
            ),
        ),
        process_markers=(),
        safety_events=(),
    )
    artifact = build_frozen_trajectory_artifact(
        case_id="synthetic-no-assistant", trajectory=trajectory
    )
    path = tmp_path / "no-assistant.json"
    path.write_bytes(artifact.stored_bytes())

    with pytest.raises(EvaluationError, match="assistant turn"):
        service.run(path)
