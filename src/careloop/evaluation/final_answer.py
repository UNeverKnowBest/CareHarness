"""Context-limited final-answer baseline with no trajectory access."""

from typing import Literal

from careloop.domain import FinalAnswerView, Finding
from careloop.evaluation.registry import EvaluationPolicyRegistry
from careloop.process.registry import ProcessPolicyRegistry, TextSignalRule


class FinalAnswerEvaluator:
    """Evaluate only the final assistant text exposed by FinalAnswerView."""

    def __init__(
        self,
        process_policy: ProcessPolicyRegistry,
        evaluation_policy: EvaluationPolicyRegistry,
    ) -> None:
        self._process_policy = process_policy
        self._evaluation_policy = evaluation_policy

    def evaluate(self, view: FinalAnswerView) -> tuple[Finding, ...]:
        if not isinstance(view, FinalAnswerView):
            raise TypeError("FinalAnswerEvaluator requires FinalAnswerView")
        folded_text = view.text.casefold()
        findings: list[Finding] = []
        for rule in self._process_policy.rules:
            outcome: Literal["present", "absent", "uncertain"] = "uncertain"
            if isinstance(rule, TextSignalRule):
                if any(
                    phrase.casefold() in folded_text for phrase in rule.present_phrases
                ):
                    outcome = "present"
                elif any(
                    phrase.casefold() in folded_text for phrase in rule.absent_phrases
                ):
                    outcome = "absent"
            findings.append(
                Finding(
                    finding_id=f"{view.turn_id}:final:{rule.rule_id}",
                    rule_id=rule.rule_id,
                    outcome=outcome,
                    turn_ids=(view.turn_id,),
                    source_ids=rule.source_ids,
                    evaluator_version=self._process_policy.evaluator_version,
                )
            )
        for safety_rule in self._evaluation_policy.safety_observations:
            findings.append(
                Finding(
                    finding_id=f"{view.turn_id}:final:{safety_rule.rule_id}",
                    rule_id=safety_rule.rule_id,
                    outcome="uncertain",
                    turn_ids=(view.turn_id,),
                    source_ids=safety_rule.source_ids,
                    evaluator_version=self._evaluation_policy.evaluator_version,
                )
            )
        return tuple(findings)
