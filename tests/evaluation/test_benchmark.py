import json
from pathlib import Path

from careloop.application import (
    EvaluateTrajectory,
    GoldCase,
    RunBenchmark,
    load_gold_case,
)
from careloop.domain import BenchmarkManifest, Trajectory

ROOT = Path(__file__).parents[2]
TRAJECTORY_ROOT = ROOT / "benchmarks" / "trajectories"
GOLD_ROOT = ROOT / "benchmarks" / "gold"
MANIFEST_PATH = ROOT / "benchmarks" / "manifest.v1.json"
PROCESS_POLICY_PATH = ROOT / "policies" / "process.v1.json"
CRISIS_POLICY_PATH = ROOT / "policies" / "crisis.v1.json"
RESOURCE_POLICY_PATH = ROOT / "policies" / "resources.v1.json"
EVALUATION_POLICY_PATH = ROOT / "policies" / "evaluation.v1.json"


def _service() -> EvaluateTrajectory:
    return EvaluateTrajectory.from_paths(
        benchmark_manifest_path=MANIFEST_PATH,
        process_policy_path=PROCESS_POLICY_PATH,
        crisis_policy_path=CRISIS_POLICY_PATH,
        resource_policy_path=RESOURCE_POLICY_PATH,
        evaluation_policy_path=EVALUATION_POLICY_PATH,
    )


def test_benchmark_evaluates_each_case_before_loading_its_gold(
    tmp_path: Path,
) -> None:
    events: list[str] = []
    real_service = _service()

    class SpyEvaluator:
        @property
        def as_of(self):  # type: ignore[no-untyped-def]
            return real_service.as_of

        def run(self, path: str | Path, *, output_path: str | Path | None = None):  # type: ignore[no-untyped-def]
            events.append(f"evaluate:{Path(path).stem}")
            return real_service.run(path, output_path=output_path)

    def spy_gold_loader(path: Path, trajectory: Trajectory) -> GoldCase:
        events.append(f"gold:{path.stem}")
        return load_gold_case(path, trajectory)

    manifest = BenchmarkManifest(
        benchmark_version="v1",
        as_of=real_service.as_of,
        case_ids=("p1-good", "p1-bad"),
        resource_registry_version="v1",
    )
    runner = RunBenchmark(
        evaluator=SpyEvaluator(),
        manifest=manifest,
        gold_loader=spy_gold_loader,
    )

    runner.run(
        trajectory_dir=TRAJECTORY_ROOT,
        gold_dir=GOLD_ROOT,
        output_path=tmp_path / "raw.jsonl",
    )

    assert events == [
        "evaluate:p1-good",
        "gold:p1-good",
        "evaluate:p1-bad",
        "gold:p1-bad",
    ]


def test_full_benchmark_preserves_manifest_order_and_exact_comparisons(
    tmp_path: Path,
) -> None:
    runner = RunBenchmark.from_paths(
        benchmark_manifest_path=MANIFEST_PATH,
        process_policy_path=PROCESS_POLICY_PATH,
        crisis_policy_path=CRISIS_POLICY_PATH,
        resource_policy_path=RESOURCE_POLICY_PATH,
        evaluation_policy_path=EVALUATION_POLICY_PATH,
    )
    output_path = tmp_path / "benchmark.v1.jsonl"

    first = runner.run(
        trajectory_dir=TRAJECTORY_ROOT,
        gold_dir=GOLD_ROOT,
        output_path=output_path,
    )
    first_bytes = output_path.read_bytes()
    second = runner.run(
        trajectory_dir=TRAJECTORY_ROOT,
        gold_dir=GOLD_ROOT,
        output_path=output_path,
    )

    assert first == second
    assert output_path.read_bytes() == first_bytes
    assert first_bytes.endswith(b"\n")
    assert b"\r" not in first_bytes
    lines = first_bytes.splitlines()
    assert len(lines) == 16
    parsed = [json.loads(line) for line in lines]
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert [record["case_id"] for record in parsed] == manifest["case_ids"]
    assert all(record["comparisons"][0]["matches"] for record in parsed)
    assert all(record["all_expected_findings_match"] for record in parsed)
    assert b"timestamp" not in first_bytes.lower()
    assert b"duration" not in first_bytes.lower()


def test_single_case_evaluation_module_has_no_gold_dependency() -> None:
    source = (
        ROOT / "src" / "careloop" / "application" / "evaluate_trajectory.py"
    ).read_text(encoding="utf-8")

    assert "gold" not in source.casefold()
