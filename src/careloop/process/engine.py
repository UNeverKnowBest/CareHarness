"""Generic deterministic execution of validated observable process rules."""

from collections.abc import Iterable
from typing import Literal

from careloop.domain import Finding, Trajectory
from careloop.process.registry import (
    MarkerCountRule,
    MarkerTransitionRule,
    ProcessRule,
    TextSignalRule,
)

FindingOutcome = Literal["present", "absent", "uncertain"]


def _ordered_unique(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def _fallback_turn_ids(
    trajectory: Trajectory, role: str | None = None
) -> tuple[str, ...]:
    role_matches = tuple(
        turn.turn_id for turn in trajectory.turns if role is None or turn.role == role
    )
    if role_matches:
        return role_matches
    return tuple(turn.turn_id for turn in trajectory.turns)


def _text_signal(
    trajectory: Trajectory, rule: TextSignalRule
) -> tuple[FindingOutcome, tuple[str, ...]]:
    relevant = tuple(turn for turn in trajectory.turns if turn.role == rule.target_role)
    present_ids = _ordered_unique(
        turn.turn_id
        for turn in relevant
        if any(
            phrase.casefold() in turn.text.casefold() for phrase in rule.present_phrases
        )
    )
    if present_ids:
        return "present", present_ids

    absent_ids = _ordered_unique(
        turn.turn_id
        for turn in relevant
        if any(
            phrase.casefold() in turn.text.casefold() for phrase in rule.absent_phrases
        )
    )
    if absent_ids:
        return "absent", absent_ids
    return "uncertain", _fallback_turn_ids(trajectory, rule.target_role)


def _marker_count(
    trajectory: Trajectory, rule: MarkerCountRule
) -> tuple[FindingOutcome, tuple[str, ...]]:
    matched_markers = tuple(
        marker
        for marker in trajectory.process_markers
        if marker.marker_type == rule.marker_type and marker.value == rule.marker_value
    )
    matched_ids = _ordered_unique(marker.turn_id for marker in matched_markers)
    if len(matched_markers) > rule.max_count:
        return "present", matched_ids
    if matched_markers:
        return "absent", matched_ids
    return "uncertain", _fallback_turn_ids(trajectory)


def _marker_transition(
    trajectory: Trajectory, rule: MarkerTransitionRule
) -> tuple[FindingOutcome, tuple[str, ...]]:
    sequence_by_turn_id = {turn.turn_id: turn.sequence for turn in trajectory.turns}
    indexed_markers = tuple(
        (index, marker)
        for index, marker in enumerate(trajectory.process_markers)
        if marker.marker_type == rule.marker_type
    )
    markers = tuple(
        marker
        for _, marker in sorted(
            indexed_markers,
            key=lambda item: (sequence_by_turn_id[item[1].turn_id], item[0]),
        )
    )
    marker_ids = _ordered_unique(marker.turn_id for marker in markers)
    unknown_ids = _ordered_unique(
        marker.turn_id for marker in markers if marker.value not in rule.allowed_values
    )
    if unknown_ids:
        return "present", unknown_ids
    if len(markers) < 2:
        return "uncertain", marker_ids or _fallback_turn_ids(trajectory)

    allowed = set(rule.allowed_transitions)
    invalid_ids: list[str] = []
    for previous, current in zip(markers, markers[1:]):
        if (previous.value, current.value) not in allowed:
            invalid_ids.extend((previous.turn_id, current.turn_id))
    if invalid_ids:
        return "present", _ordered_unique(invalid_ids)
    return "absent", marker_ids


def evaluate_rule(
    trajectory: Trajectory, rule: ProcessRule, evaluator_version: Literal["v1"]
) -> Finding:
    """Evaluate one registry rule and construct validated evidence."""
    if isinstance(rule, TextSignalRule):
        outcome, turn_ids = _text_signal(trajectory, rule)
    elif isinstance(rule, MarkerCountRule):
        outcome, turn_ids = _marker_count(trajectory, rule)
    else:
        outcome, turn_ids = _marker_transition(trajectory, rule)

    finding = Finding(
        finding_id=f"{trajectory.trajectory_id}:{rule.rule_id}",
        rule_id=rule.rule_id,
        outcome=outcome,
        turn_ids=turn_ids,
        source_ids=rule.source_ids,
        evaluator_version=evaluator_version,
    )
    trajectory.validate_finding(finding)
    return finding


def evaluate_rules(
    trajectory: Trajectory,
    rules: Iterable[ProcessRule],
    evaluator_version: Literal["v1"],
) -> tuple[Finding, ...]:
    return tuple(evaluate_rule(trajectory, rule, evaluator_version) for rule in rules)
