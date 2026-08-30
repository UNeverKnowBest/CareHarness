"""Observable generic CBT-informed process evaluator."""

from careloop.domain import Finding, Trajectory
from careloop.process.engine import evaluate_rules
from careloop.process.registry import ProcessPolicyRegistry


class CBTInformedEvaluator:
    def __init__(self, policy: ProcessPolicyRegistry) -> None:
        self._policy = policy

    def evaluate(self, trajectory: Trajectory) -> tuple[Finding, ...]:
        rules = (
            rule for rule in self._policy.rules if rule.evaluator == "cbt_informed"
        )
        return evaluate_rules(trajectory, rules, self._policy.evaluator_version)
