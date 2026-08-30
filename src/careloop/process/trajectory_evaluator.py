"""Stable aggregate evaluation across all process-policy rules."""

from careloop.domain import Finding, Trajectory
from careloop.process.engine import evaluate_rules
from careloop.process.registry import ProcessPolicyRegistry


class ProcessTrajectoryEvaluator:
    """Pure trajectory-aware evaluator that cannot receive benchmark gold."""

    def __init__(self, policy: ProcessPolicyRegistry) -> None:
        self._policy = policy

    def evaluate(self, trajectory: Trajectory) -> tuple[Finding, ...]:
        return evaluate_rules(
            trajectory, self._policy.rules, self._policy.evaluator_version
        )
