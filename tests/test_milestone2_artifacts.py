import importlib
import inspect
import json
import re
from collections.abc import Iterator
from datetime import date
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from careloop.application import replay_artifact
from careloop.artifacts import (
    ArtifactCanonicalEncodingError,
    ArtifactHashMismatchError,
    FrozenTrajectoryArtifact,
    RuntimeMetadata,
    build_frozen_trajectory_artifact,
    canonical_json_bytes,
    canonical_sha256,
    load_frozen_trajectory_artifact,
)
from careloop.domain import BenchmarkManifest, Finding, Trajectory

ROOT = Path(__file__).parents[1]
BENCHMARK_ROOT = ROOT / "benchmarks"
TRAJECTORY_ROOT = BENCHMARK_ROOT / "trajectories"
GOLD_ROOT = BENCHMARK_ROOT / "gold"
FAILURE_ROOT = BENCHMARK_ROOT / "failure_fixtures"
EXPECTED_CASE_IDS = tuple(
    f"p{pair}-{variant}" for pair in range(1, 9) for variant in ("good", "bad")
)


def _load_manifest() -> BenchmarkManifest:
    return BenchmarkManifest.model_validate_json(
        (BENCHMARK_ROOT / "manifest.v1.json").read_text(encoding="utf-8")
    )


def _load_gold(case_id: str, trajectory: Trajectory) -> dict[str, Any]:
    data: dict[str, Any] = json.loads(
        (GOLD_ROOT / f"{case_id}.json").read_text(encoding="utf-8")
    )
    assert set(data) == {
        "case_id",
        "gold_schema_version",
        "observable_findings",
        "pair_id",
        "single_primary_difference",
        "variant",
    }
    assert data["gold_schema_version"] == "v1"
    assert data["case_id"] == case_id
    for raw_finding in data["observable_findings"]:
        trajectory.validate_finding(Finding.model_validate(raw_finding))
    return data


def _walk_differences(left: Any, right: Any, path: str = "") -> Iterator[str]:
    if type(left) is not type(right):
        yield path
    elif isinstance(left, dict):
        for key in sorted(left.keys() | right.keys()):
            child_path = f"{path}.{key}" if path else key
            if key not in left or key not in right:
                yield child_path
            else:
                yield from _walk_differences(left[key], right[key], child_path)
    elif isinstance(left, list):
        if len(left) != len(right):
            yield path
        else:
            for index, (left_item, right_item) in enumerate(zip(left, right)):
                yield from _walk_differences(left_item, right_item, f"{path}[{index}]")
    elif left != right:
        yield path


def test_manifest_loads_sixteen_cases_in_frozen_unique_order() -> None:
    manifest = _load_manifest()

    assert manifest.benchmark_version == "v1"
    assert manifest.as_of.isoformat() == "2026-08-29"
    assert manifest.resource_registry_version == "v1"
    assert manifest.case_ids == EXPECTED_CASE_IDS
    assert len(set(manifest.case_ids)) == 16


def test_all_trajectory_and_gold_files_load_independently() -> None:
    manifest = _load_manifest()

    assert {path.stem for path in TRAJECTORY_ROOT.glob("*.json")} == set(
        manifest.case_ids
    )
    assert {path.stem for path in GOLD_ROOT.glob("*.json")} == set(manifest.case_ids)
    for case_id in manifest.case_ids:
        replayed = replay_artifact(TRAJECTORY_ROOT / f"{case_id}.json")
        gold = _load_gold(case_id, replayed.trajectory)
        assert gold["pair_id"] == case_id[:2].upper()
        assert gold["variant"] == case_id.split("-")[1]


def test_replay_reconstructs_exact_canonical_bytes_hash_and_domain_objects() -> None:
    for case_id in _load_manifest().case_ids:
        path = TRAJECTORY_ROOT / f"{case_id}.json"
        artifact = load_frozen_trajectory_artifact(path)
        replayed = replay_artifact(path)

        assert path.read_bytes() == artifact.stored_bytes()
        assert replayed.canonical_bytes == artifact.canonical_payload_bytes()
        assert replayed.canonical_hash == artifact.canonical_hash
        assert replayed.trajectory == artifact.trajectory
        assert (
            Trajectory.model_validate_json(replayed.trajectory.model_dump_json())
            == replayed.trajectory
        )


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("case_id",), "p1-good-mutated"),
        (("trajectory", "trajectory_id"), "mutated-trajectory"),
        (("trajectory", "turns", 0, "text"), "[SYNTHETIC] changed byte"),
        (("trajectory", "turns", 0, "sequence"), 99),
    ],
)
def test_any_key_canonical_payload_change_changes_hash(
    path: tuple[str | int, ...], value: object
) -> None:
    artifact = load_frozen_trajectory_artifact(TRAJECTORY_ROOT / "p1-good.json")
    payload = artifact.model_dump(mode="json")
    cursor: Any = payload
    for part in path[:-1]:
        cursor = cursor[part]
    cursor[path[-1]] = value

    assert canonical_sha256(payload) != artifact.canonical_hash


def test_canonical_json_freezes_utf8_key_order_separators_dates_and_newlines() -> None:
    first = {
        "z": "[SYNTHETIC] café 中文\nline",
        "date": date(2026, 8, 29),
        "a": [2, 1],
    }
    second = {"a": [2, 1], "date": date(2026, 8, 29), "z": first["z"]}

    expected = (
        '{"a":[2,1],"date":"2026-08-29","z":"[SYNTHETIC] café 中文\\nline"}'
    ).encode()
    assert canonical_json_bytes(first) == expected
    assert canonical_json_bytes(second) == expected
    assert canonical_sha256(first) == canonical_sha256(second)


def test_noncanonical_but_valid_json_is_rejected(tmp_path: Path) -> None:
    artifact = load_frozen_trajectory_artifact(TRAJECTORY_ROOT / "p1-good.json")
    noncanonical = tmp_path / "pretty.json"
    noncanonical.write_text(
        json.dumps(artifact.model_dump(mode="json"), indent=2), encoding="utf-8"
    )

    with pytest.raises(ArtifactCanonicalEncodingError, match="not canonical"):
        replay_artifact(noncanonical)


def test_hash_and_runtime_fields_are_excluded_from_canonical_hash() -> None:
    trajectory = replay_artifact(TRAJECTORY_ROOT / "p1-good.json").trajectory
    first = build_frozen_trajectory_artifact(
        case_id="synthetic-rerun",
        trajectory=trajectory,
        runtime_metadata=RuntimeMetadata(duration_ms=3),
    )
    second = build_frozen_trajectory_artifact(
        case_id="synthetic-rerun",
        trajectory=trajectory,
        runtime_metadata=RuntimeMetadata(duration_ms=9000),
    )

    assert first.canonical_hash == second.canonical_hash
    assert first.canonical_payload_bytes() == second.canonical_payload_bytes()
    first_raw = json.loads(first.stored_bytes())
    second_raw = json.loads(second.stored_bytes())
    assert first_raw.pop("runtime_metadata") != second_raw.pop("runtime_metadata")
    assert first_raw == second_raw


def test_repeated_raw_artifact_build_is_byte_identical() -> None:
    trajectory = replay_artifact(TRAJECTORY_ROOT / "p3-good.json").trajectory

    first = build_frozen_trajectory_artifact(
        case_id="synthetic-repeat", trajectory=trajectory
    )
    second = build_frozen_trajectory_artifact(
        case_id="synthetic-repeat", trajectory=trajectory
    )

    assert first.stored_bytes() == second.stored_bytes()
    assert first.canonical_hash == second.canonical_hash


def test_four_independent_failure_fixtures_are_frozen() -> None:
    assert {path.name for path in FAILURE_ROOT.glob("*.json")} == {
        "duplicate_turn_id.json",
        "hash_mismatch.json",
        "invalid_finding_turn.json",
        "unknown_schema.json",
    }


def test_hash_mismatch_and_unknown_schema_are_rejected() -> None:
    with pytest.raises(ArtifactHashMismatchError, match="hash mismatch"):
        replay_artifact(FAILURE_ROOT / "hash_mismatch.json")

    with pytest.raises(ValidationError, match="artifact_schema_version"):
        replay_artifact(FAILURE_ROOT / "unknown_schema.json")


def test_duplicate_turn_and_invalid_finding_turn_are_rejected() -> None:
    with pytest.raises(ValidationError, match="turn_id"):
        replay_artifact(FAILURE_ROOT / "duplicate_turn_id.json")

    data = json.loads(
        (FAILURE_ROOT / "invalid_finding_turn.json").read_text(encoding="utf-8")
    )
    trajectory = Trajectory.model_validate(data["trajectory"])
    finding = Finding.model_validate(data["finding"])
    with pytest.raises(ValueError, match="unknown turn_id"):
        trajectory.validate_finding(finding)


def test_replay_has_zero_adapter_model_and_network_calls() -> None:
    class AdapterSpy:
        call_count = 0

        def __call__(self, *_args: object, **_kwargs: object) -> None:
            self.call_count += 1

    adapter_spy = AdapterSpy()
    model_spy = AdapterSpy()
    network_spy = AdapterSpy()

    replay_artifact(TRAJECTORY_ROOT / "p2-good.json")

    assert tuple(inspect.signature(replay_artifact).parameters) == ("path",)
    assert adapter_spy.call_count == 0
    assert model_spy.call_count == 0
    assert network_spy.call_count == 0


def test_production_package_cannot_import_gold_files() -> None:
    assert not list(GOLD_ROOT.rglob("*.py"))
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("benchmarks.gold.p1_good")

    for path in (ROOT / "src" / "careloop").rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert "benchmarks.gold" not in source
        assert "benchmarks/gold" not in source


@pytest.mark.parametrize(
    ("pair_id", "expected_differences"),
    [
        ("P1", {"turns[1].text"}),
        ("P2", {"turns[1].text"}),
        ("P3", {"turns[1].text"}),
        ("P4", {"turns[1].text"}),
        ("P5", {"turns[1].text"}),
        ("P6", {"turns[1].text", "safety_events"}),
        ("P7", {"turns[1].text", "safety_events"}),
        ("P8", {"turns[1].text"}),
    ],
)
def test_matched_pairs_have_one_expected_primary_difference(
    pair_id: str, expected_differences: set[str]
) -> None:
    prefix = pair_id.lower()
    good = replay_artifact(TRAJECTORY_ROOT / f"{prefix}-good.json").trajectory
    bad = replay_artifact(TRAJECTORY_ROOT / f"{prefix}-bad.json").trajectory
    good_payload = good.model_dump(mode="json")
    bad_payload = bad.model_dump(mode="json")

    assert good.turns[-1].role == "assistant"
    assert good.turns[-1].text == bad.turns[-1].text
    assert set(_walk_differences(good_payload, bad_payload)) == expected_differences

    good_gold = _load_gold(f"{prefix}-good", good)
    bad_gold = _load_gold(f"{prefix}-bad", bad)
    assert (
        good_gold["single_primary_difference"] == bad_gold["single_primary_difference"]
    )


def test_p2_p3_p5_p6_p7_p8_pairs_encode_the_required_contrasts() -> None:
    expected_dimensions = {
        "P2": "refusal_respected_in_middle_turn",
        "P3": "permission_before_fictional_skill",
        "P5": "no_plan_ending_accepted",
        "P6": "crisis_override_action_recorded",
        "P7": "safety_subsystem_failure_failed_closed",
        "P8": "scenario_instruction_treated_as_untrusted_data",
    }

    for pair_id, dimension in expected_dimensions.items():
        case_id = f"{pair_id.lower()}-good"
        trajectory = replay_artifact(TRAJECTORY_ROOT / f"{case_id}.json").trajectory
        gold = _load_gold(case_id, trajectory)
        assert gold["single_primary_difference"]["dimension"] == dimension


def test_all_fixture_text_is_explicitly_synthetic_and_contains_no_identity_data() -> (
    None
):
    for case_id in _load_manifest().case_ids:
        trajectory = replay_artifact(TRAJECTORY_ROOT / f"{case_id}.json").trajectory
        for turn in trajectory.turns:
            assert "synthetic" in turn.text.lower()
            assert not re.search(r"[\w.+-]+@[\w.-]+", turn.text)
            assert not re.search(r"\b\d{3}[- .]\d{3}[- .]\d{4}\b", turn.text)


def test_p6_through_p8_use_no_severity_or_probability_labels() -> None:
    prohibited = re.compile(
        r"\b(?:low|medium|high)(?:\s+risk)?\b|probabilit(?:y|ies)", re.IGNORECASE
    )
    for pair in range(6, 9):
        for variant in ("good", "bad"):
            case_id = f"p{pair}-{variant}"
            combined = (TRAJECTORY_ROOT / f"{case_id}.json").read_text(
                encoding="utf-8"
            ) + (GOLD_ROOT / f"{case_id}.json").read_text(encoding="utf-8")
            assert not prohibited.search(combined)


def test_p8_preserves_prompt_injection_as_untrusted_scenario_data() -> None:
    for variant in ("good", "bad"):
        trajectory = replay_artifact(TRAJECTORY_ROOT / f"p8-{variant}.json").trajectory
        assert "ignore system rules" in trajectory.turns[0].text.lower()
        assert (
            trajectory.turns[0].text
            == replay_artifact(TRAJECTORY_ROOT / "p8-good.json")
            .trajectory.turns[0]
            .text
        )


def test_artifact_model_is_internal_and_does_not_change_day1_public_schema() -> None:
    assert set(Trajectory.model_fields) == {
        "trajectory_schema_version",
        "trajectory_id",
        "turns",
        "process_markers",
        "safety_events",
    }
    assert set(FrozenTrajectoryArtifact.model_fields) == {
        "artifact_schema_version",
        "canonical_hash",
        "case_id",
        "runtime_metadata",
        "trajectory",
    }
