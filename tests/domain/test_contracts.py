from datetime import date
from importlib import import_module
from types import ModuleType

import pytest
from pydantic import ValidationError


@pytest.fixture
def domain() -> ModuleType:
    return import_module("careloop.domain")


def make_turn(
    domain: ModuleType,
    *,
    turn_id: str,
    sequence: int,
    role: str,
    text: str,
) -> object:
    return domain.Turn(
        turn_id=turn_id,
        sequence=sequence,
        role=role,
        text=text,
    )


def make_trajectory(domain: ModuleType) -> object:
    return domain.Trajectory(
        trajectory_schema_version="v1",
        trajectory_id="trajectory-synthetic-001",
        turns=(
            make_turn(
                domain,
                turn_id="turn-001",
                sequence=0,
                role="user",
                text="Synthetic user turn.",
            ),
            make_turn(
                domain,
                turn_id="turn-002",
                sequence=1,
                role="assistant",
                text="Synthetic assistant turn.",
            ),
        ),
        process_markers=(
            domain.ProcessMarker(
                marker_id="marker-001",
                turn_id="turn-002",
                marker_type="observable-marker",
                value="synthetic-value",
                source_ids=("source-process-001",),
                process_policy_version="v1",
            ),
        ),
        safety_events=(
            domain.SafetyEvent(
                event_id="event-001",
                triggering_turn_ids=("turn-001",),
                action=domain.SafetyAction.CONTINUE_SUPPORT,
                requires_override=False,
                normal_flow_suppressed=False,
                source_ids=("source-crisis-001",),
                resource_ids=(),
                crisis_policy_version="v1",
            ),
        ),
    )


def make_finding(domain: ModuleType, *turn_ids: str) -> object:
    return domain.Finding(
        finding_id="finding-001",
        rule_id="rule-observable-001",
        outcome="present",
        turn_ids=turn_ids,
        source_ids=("source-evaluator-001",),
        evaluator_version="v1",
    )


def make_resource(domain: ModuleType, **overrides: object) -> object:
    data: dict[str, object] = {
        "resource_id": "resource-synthetic-001",
        "name": "Synthetic Resource",
        "jurisdiction": "ZZ-SYNTHETIC",
        "contact": "synthetic-contact",
        "source_url": "https://example.invalid/resource-source",
        "is_allowlisted": True,
        "verified_on": date(2026, 1, 1),
        "expires_on": date(2026, 12, 31),
        "resource_registry_version": "v1",
    }
    data.update(overrides)
    return domain.CrisisResource(**data)


def test_valid_trajectory_round_trip(domain: ModuleType) -> None:
    trajectory = make_trajectory(domain)

    restored = domain.Trajectory.model_validate_json(trajectory.model_dump_json())

    assert restored == trajectory


def test_duplicate_turn_id_is_rejected(domain: ModuleType) -> None:
    turns = (
        make_turn(domain, turn_id="duplicate", sequence=0, role="user", text="a"),
        make_turn(
            domain,
            turn_id="duplicate",
            sequence=1,
            role="assistant",
            text="b",
        ),
    )

    with pytest.raises(ValidationError, match="turn_id"):
        domain.Trajectory(
            trajectory_schema_version="v1",
            trajectory_id="trajectory-duplicate",
            turns=turns,
            process_markers=(),
            safety_events=(),
        )


def test_non_monotonic_turn_sequence_is_rejected(domain: ModuleType) -> None:
    turns = (
        make_turn(domain, turn_id="turn-001", sequence=1, role="user", text="a"),
        make_turn(domain, turn_id="turn-002", sequence=1, role="assistant", text="b"),
    )

    with pytest.raises(ValidationError, match="sequence"):
        domain.Trajectory(
            trajectory_schema_version="v1",
            trajectory_id="trajectory-sequence",
            turns=turns,
            process_markers=(),
            safety_events=(),
        )


def test_empty_trajectory_is_rejected(domain: ModuleType) -> None:
    with pytest.raises(ValidationError, match="turns"):
        domain.Trajectory(
            trajectory_schema_version="v1",
            trajectory_id="trajectory-empty",
            turns=(),
            process_markers=(),
            safety_events=(),
        )


def test_empty_turn_id_and_unknown_role_are_rejected(domain: ModuleType) -> None:
    with pytest.raises(ValidationError, match="turn_id"):
        make_turn(domain, turn_id=" ", sequence=0, role="user", text="synthetic")

    with pytest.raises(ValidationError, match="role"):
        make_turn(
            domain,
            turn_id="turn-role",
            sequence=0,
            role="system",
            text="synthetic",
        )


def test_unknown_process_marker_turn_reference_is_rejected(
    domain: ModuleType,
) -> None:
    marker = domain.ProcessMarker(
        marker_id="marker-missing",
        turn_id="turn-missing",
        marker_type="observable-marker",
        value="synthetic-value",
        source_ids=("source-process-001",),
        process_policy_version="v1",
    )

    with pytest.raises(ValidationError, match="turn-missing"):
        domain.Trajectory(
            trajectory_schema_version="v1",
            trajectory_id="trajectory-missing-marker-reference",
            turns=(
                make_turn(
                    domain,
                    turn_id="turn-001",
                    sequence=0,
                    role="user",
                    text="synthetic",
                ),
            ),
            process_markers=(marker,),
            safety_events=(),
        )


def test_empty_finding_turn_references_are_rejected(domain: ModuleType) -> None:
    with pytest.raises(ValidationError, match="turn_ids"):
        make_finding(domain)


def test_unknown_finding_turn_reference_is_rejected(domain: ModuleType) -> None:
    trajectory = make_trajectory(domain)
    finding = make_finding(domain, "turn-missing")

    with pytest.raises(ValueError, match="turn-missing"):
        trajectory.validate_finding(finding)


def test_valid_finding_turn_references_are_accepted(domain: ModuleType) -> None:
    trajectory = make_trajectory(domain)
    finding = make_finding(domain, "turn-001", "turn-002")

    trajectory.validate_finding(finding)


def test_empty_safety_event_turn_references_are_rejected(domain: ModuleType) -> None:
    with pytest.raises(ValidationError, match="triggering_turn_ids"):
        domain.SafetyEvent(
            event_id="event-empty",
            triggering_turn_ids=(),
            action=domain.SafetyAction.PAUSE_AND_CLARIFY_NOW,
            requires_override=False,
            normal_flow_suppressed=False,
            source_ids=("source-crisis-001",),
            resource_ids=(),
            crisis_policy_version="v1",
        )


def test_unknown_safety_event_turn_reference_is_rejected(domain: ModuleType) -> None:
    event = domain.SafetyEvent(
        event_id="event-missing",
        triggering_turn_ids=("turn-missing",),
        action=domain.SafetyAction.PAUSE_AND_CLARIFY_NOW,
        requires_override=False,
        normal_flow_suppressed=False,
        source_ids=("source-crisis-001",),
        resource_ids=(),
        crisis_policy_version="v1",
    )

    with pytest.raises(ValidationError, match="turn-missing"):
        domain.Trajectory(
            trajectory_schema_version="v1",
            trajectory_id="trajectory-missing-event-reference",
            turns=(
                make_turn(
                    domain,
                    turn_id="turn-001",
                    sequence=0,
                    role="user",
                    text="synthetic",
                ),
            ),
            process_markers=(),
            safety_events=(event,),
        )


def test_override_requires_normal_flow_suppression(domain: ModuleType) -> None:
    with pytest.raises(ValidationError, match="normal_flow_suppressed"):
        domain.SafetyEvent(
            event_id="event-override",
            triggering_turn_ids=("turn-001",),
            action=domain.SafetyAction.CONNECT_HUMAN_HELP_NOW,
            requires_override=True,
            normal_flow_suppressed=False,
            source_ids=("source-crisis-001",),
            resource_ids=(),
            crisis_policy_version="v1",
        )


def test_resource_expiry_cannot_precede_verification(domain: ModuleType) -> None:
    with pytest.raises(ValidationError, match="expires_on"):
        make_resource(
            domain,
            verified_on=date(2026, 2, 1),
            expires_on=date(2026, 1, 31),
        )


def test_resource_must_be_allowlisted(domain: ModuleType) -> None:
    with pytest.raises(ValidationError, match="is_allowlisted"):
        make_resource(domain, is_allowlisted=False)


def test_safety_action_contains_only_approved_system_actions(
    domain: ModuleType,
) -> None:
    assert {action.value for action in domain.SafetyAction} == {
        "continue_support",
        "pause_and_clarify_now",
        "connect_human_help_now",
        "seek_emergency_help_now",
    }


@pytest.mark.parametrize(
    ("model_name", "valid_data", "version_field"),
    [
        (
            "EvaluationManifest",
            {
                "trajectory_schema_version": "v1",
                "process_policy_version": "v1",
                "ethical_policy_version": "v1",
                "crisis_policy_version": "v1",
                "resource_registry_version": "v1",
                "evaluator_version": "v1",
            },
            "ethical_policy_version",
        ),
        (
            "BenchmarkManifest",
            {
                "benchmark_version": "v1",
                "as_of": date(2026, 1, 1),
                "case_ids": ("case-synthetic-001",),
                "resource_registry_version": "v1",
            },
            "benchmark_version",
        ),
    ],
)
def test_unknown_manifest_version_fails_visibly(
    domain: ModuleType,
    model_name: str,
    valid_data: dict[str, object],
    version_field: str,
) -> None:
    valid_data[version_field] = "v999"

    with pytest.raises(ValidationError, match=version_field):
        getattr(domain, model_name)(**valid_data)


def test_unknown_embedded_schema_and_policy_versions_fail_visibly(
    domain: ModuleType,
) -> None:
    with pytest.raises(ValidationError, match="trajectory_schema_version"):
        domain.Trajectory(
            trajectory_schema_version="v999",
            trajectory_id="trajectory-version",
            turns=(
                make_turn(
                    domain,
                    turn_id="turn-001",
                    sequence=0,
                    role="user",
                    text="synthetic",
                ),
            ),
            process_markers=(),
            safety_events=(),
        )

    with pytest.raises(ValidationError, match="process_policy_version"):
        domain.ProcessMarker(
            marker_id="marker-version",
            turn_id="turn-001",
            marker_type="observable-marker",
            value="synthetic-value",
            source_ids=("source-process-001",),
            process_policy_version="v999",
        )


def test_unknown_crisis_resource_and_evaluator_versions_fail_visibly(
    domain: ModuleType,
) -> None:
    with pytest.raises(ValidationError, match="crisis_policy_version"):
        domain.SafetyEvent(
            event_id="event-version",
            triggering_turn_ids=("turn-001",),
            action=domain.SafetyAction.CONTINUE_SUPPORT,
            requires_override=False,
            normal_flow_suppressed=False,
            source_ids=("source-crisis-001",),
            resource_ids=(),
            crisis_policy_version="v999",
        )

    with pytest.raises(ValidationError, match="resource_registry_version"):
        make_resource(domain, resource_registry_version="v999")

    with pytest.raises(ValidationError, match="evaluator_version"):
        domain.Finding(
            finding_id="finding-version",
            rule_id="rule-observable-001",
            outcome="uncertain",
            turn_ids=("turn-001",),
            source_ids=("source-evaluator-001",),
            evaluator_version="v999",
        )


def test_forbidden_clinical_fields_do_not_exist(domain: ModuleType) -> None:
    forbidden = {
        "risk_score",
        "risk_level",
        "suicide_probability",
        "diagnosis",
        "clinical_disposition",
    }
    model_names = (
        "Turn",
        "Trajectory",
        "ProcessMarker",
        "SafetyEvent",
        "Finding",
        "EvaluationManifest",
        "BenchmarkManifest",
        "CrisisResource",
        "FinalAnswerView",
    )

    for model_name in model_names:
        assert forbidden.isdisjoint(getattr(domain, model_name).model_fields)


def test_public_model_fields_match_frozen_wire_contract(domain: ModuleType) -> None:
    expected_fields = {
        "Turn": {"turn_id", "sequence", "role", "text"},
        "Trajectory": {
            "trajectory_schema_version",
            "trajectory_id",
            "turns",
            "process_markers",
            "safety_events",
        },
        "ProcessMarker": {
            "marker_id",
            "turn_id",
            "marker_type",
            "value",
            "source_ids",
            "process_policy_version",
        },
        "SafetyEvent": {
            "event_id",
            "triggering_turn_ids",
            "action",
            "requires_override",
            "normal_flow_suppressed",
            "source_ids",
            "resource_ids",
            "crisis_policy_version",
        },
        "Finding": {
            "finding_id",
            "rule_id",
            "outcome",
            "turn_ids",
            "source_ids",
            "evaluator_version",
        },
        "EvaluationManifest": {
            "trajectory_schema_version",
            "process_policy_version",
            "ethical_policy_version",
            "crisis_policy_version",
            "resource_registry_version",
            "evaluator_version",
        },
        "BenchmarkManifest": {
            "benchmark_version",
            "as_of",
            "case_ids",
            "resource_registry_version",
        },
        "CrisisResource": {
            "resource_id",
            "name",
            "jurisdiction",
            "contact",
            "source_url",
            "is_allowlisted",
            "verified_on",
            "expires_on",
            "resource_registry_version",
        },
        "FinalAnswerView": {"text", "turn_id"},
    }

    for model_name, field_names in expected_fields.items():
        assert set(getattr(domain, model_name).model_fields) == field_names


def test_final_answer_view_has_only_text_and_turn_id(domain: ModuleType) -> None:
    assert set(domain.FinalAnswerView.model_fields) == {"text", "turn_id"}

    with pytest.raises(ValidationError, match="trajectory"):
        domain.FinalAnswerView(
            text="Synthetic final answer.",
            turn_id="turn-002",
            trajectory="not-allowed",
        )


def test_public_models_reject_unknown_fields(domain: ModuleType) -> None:
    with pytest.raises(ValidationError, match="unexpected"):
        domain.Turn(
            turn_id="turn-extra",
            sequence=0,
            role="user",
            text="synthetic",
            unexpected="not-allowed",
        )


def test_benchmark_manifest_rejects_duplicate_case_ids(domain: ModuleType) -> None:
    with pytest.raises(ValidationError, match="case_ids"):
        domain.BenchmarkManifest(
            benchmark_version="v1",
            as_of=date(2026, 1, 1),
            case_ids=("case-synthetic-001", "case-synthetic-001"),
            resource_registry_version="v1",
        )
