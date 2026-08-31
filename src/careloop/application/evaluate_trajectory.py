"""Application orchestration for one frozen trajectory evaluation."""

from datetime import date
from pathlib import Path
from typing import Self

from careloop.artifacts import load_frozen_trajectory_artifact
from careloop.domain import (
    BenchmarkManifest,
    EvaluationManifest,
    FinalAnswerView,
    Trajectory,
)
from careloop.evaluation import (
    FinalAnswerEvaluator,
    ResourceReferenceEvidence,
    SafetyArtifactEvaluator,
    TrajectoryEvaluationResult,
    TrajectoryEvaluator,
    load_evaluation_policy,
)
from careloop.process import ProcessTrajectoryEvaluator, load_process_policy
from careloop.safety import load_crisis_policy, load_resource_registry
from careloop.safety.resource_registry import ResourcePolicyRegistry


class EvaluationError(ValueError):
    """Raised when a valid artifact cannot satisfy the evaluation contract."""


def load_benchmark_manifest(path: str | Path) -> BenchmarkManifest:
    return BenchmarkManifest.model_validate_json(Path(path).read_text(encoding="utf-8"))


class EvaluateTrajectory:
    """Validate one artifact and run isolated final and complete evaluators."""

    def __init__(
        self,
        *,
        final_answer_evaluator: FinalAnswerEvaluator,
        trajectory_evaluator: TrajectoryEvaluator,
        evaluation_manifest: EvaluationManifest,
        resource_policy: ResourcePolicyRegistry,
        as_of: date,
    ) -> None:
        self._final_answer_evaluator = final_answer_evaluator
        self._trajectory_evaluator = trajectory_evaluator
        self._evaluation_manifest = evaluation_manifest
        self._resource_policy = resource_policy
        self._as_of = as_of

    @property
    def as_of(self) -> date:
        return self._as_of

    @classmethod
    def from_paths(
        cls,
        *,
        benchmark_manifest_path: str | Path,
        process_policy_path: str | Path,
        crisis_policy_path: str | Path,
        resource_policy_path: str | Path,
        evaluation_policy_path: str | Path,
    ) -> Self:
        benchmark_manifest = load_benchmark_manifest(benchmark_manifest_path)
        process_policy = load_process_policy(process_policy_path)
        crisis_policy = load_crisis_policy(crisis_policy_path)
        resource_policy = load_resource_registry(resource_policy_path)
        evaluation_policy = load_evaluation_policy(evaluation_policy_path)
        if (
            benchmark_manifest.resource_registry_version
            != resource_policy.resource_registry_version
        ):
            raise EvaluationError(
                "benchmark and resource registry versions do not match"
            )
        if process_policy.evaluator_version != evaluation_policy.evaluator_version:
            raise EvaluationError("process and evaluation versions do not match")
        final_evaluator = FinalAnswerEvaluator(process_policy, evaluation_policy)
        complete_evaluator = TrajectoryEvaluator(
            ProcessTrajectoryEvaluator(process_policy),
            SafetyArtifactEvaluator(
                evaluation_policy,
                crisis_policy,
                resource_policy,
                as_of=benchmark_manifest.as_of,
            ),
        )
        evaluation_manifest = EvaluationManifest(
            trajectory_schema_version="v1",
            process_policy_version=process_policy.process_policy_version,
            ethical_policy_version="v1",
            crisis_policy_version=crisis_policy.crisis_policy_version,
            resource_registry_version=resource_policy.resource_registry_version,
            evaluator_version=evaluation_policy.evaluator_version,
        )
        return cls(
            final_answer_evaluator=final_evaluator,
            trajectory_evaluator=complete_evaluator,
            evaluation_manifest=evaluation_manifest,
            resource_policy=resource_policy,
            as_of=benchmark_manifest.as_of,
        )

    @staticmethod
    def _final_answer_view(trajectory: Trajectory) -> FinalAnswerView:
        for turn in reversed(trajectory.turns):
            if turn.role == "assistant":
                return FinalAnswerView(text=turn.text, turn_id=turn.turn_id)
        raise EvaluationError("trajectory must contain an assistant turn")

    def _resource_references(
        self, trajectory: Trajectory
    ) -> tuple[ResourceReferenceEvidence, ...]:
        referenced_ids = tuple(
            dict.fromkeys(
                resource_id
                for event in trajectory.safety_events
                for resource_id in event.resource_ids
            )
        )
        resources_by_id = {
            resource.resource_id: resource
            for resource in self._resource_policy.resources
        }
        return tuple(
            ResourceReferenceEvidence(
                resource_id=resource_id,
                registered=resource_id in resources_by_id,
                resource=resources_by_id.get(resource_id),
            )
            for resource_id in referenced_ids
        )

    def run(
        self,
        path: str | Path,
        *,
        output_path: str | Path | None = None,
    ) -> TrajectoryEvaluationResult:
        artifact = load_frozen_trajectory_artifact(path)
        final_answer = self._final_answer_view(artifact.trajectory)
        result = TrajectoryEvaluationResult(
            result_schema_version="v1",
            case_id=artifact.case_id,
            canonical_hash=artifact.canonical_hash,
            evaluation_manifest=self._evaluation_manifest,
            as_of=self._as_of,
            trajectory=artifact.trajectory,
            final_answer=final_answer,
            final_answer_findings=self._final_answer_evaluator.evaluate(final_answer),
            trajectory_findings=self._trajectory_evaluator.evaluate(
                artifact.trajectory
            ),
            resource_references=self._resource_references(artifact.trajectory),
        )
        if output_path is not None:
            destination = Path(output_path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(result.canonical_bytes())
        return result
