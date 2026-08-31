"""Deterministic ethical output gate executed before output visibility."""

from dataclasses import dataclass

from careloop.domain import Finding, Turn
from careloop.safety.registry import EthicalPolicyRegistry


@dataclass(frozen=True, slots=True)
class EthicalOutputDecision:
    allowed: bool
    findings: tuple[Finding, ...]


class EthicalOutputPolicy:
    def __init__(self, policy: EthicalPolicyRegistry) -> None:
        self._policy = policy

    def evaluate(self, output: Turn, *, override_active: bool) -> EthicalOutputDecision:
        if output.role != "assistant":
            raise ValueError("ethical output policy requires an assistant turn")
        folded_text = output.text.casefold()
        findings: list[Finding] = []
        for rule in self._policy.rules:
            if rule.only_during_override and not override_active:
                continue
            if not any(phrase.casefold() in folded_text for phrase in rule.phrases):
                continue
            findings.append(
                Finding(
                    finding_id=f"{output.turn_id}:{rule.rule_id}",
                    rule_id=rule.rule_id,
                    outcome="present",
                    turn_ids=(output.turn_id,),
                    source_ids=rule.source_ids,
                    evaluator_version=self._policy.evaluator_version,
                )
            )
        frozen_findings = tuple(findings)
        return EthicalOutputDecision(
            allowed=not frozen_findings,
            findings=frozen_findings,
        )
