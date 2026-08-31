"""Complete ordered-trajectory evaluation without benchmark gold."""

from careloop.domain import Finding, Trajectory
from careloop.evaluation.safety_artifact import SafetyArtifactEvaluator
from careloop.process import ProcessTrajectoryEvaluator


class TrajectoryEvaluator:
    """Combine stable process and safety-artifact evidence ledgers."""

    def __init__(
        self,
        process_evaluator: ProcessTrajectoryEvaluator,
        safety_evaluator: SafetyArtifactEvaluator,
    ) -> None:
        self._process_evaluator = process_evaluator
        self._safety_evaluator = safety_evaluator

    def evaluate(self, trajectory: Trajectory) -> tuple[Finding, ...]:
        return self._process_evaluator.evaluate(
            trajectory
        ) + self._safety_evaluator.evaluate(trajectory)
