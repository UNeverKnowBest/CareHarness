"""Exact-tag detector for frozen synthetic control-flow fixtures only."""

from dataclasses import dataclass

from careloop.domain import SafetyAction, Turn
from careloop.safety.registry import CrisisPolicyRegistry


@dataclass(frozen=True, slots=True)
class SafetyDetection:
    signal_id: str | None
    action: SafetyAction
    requires_override: bool
    source_ids: tuple[str, ...]


class SyntheticSafetySignalDetector:
    """Match only registry phrases; this is not a real-world detector."""

    def __init__(self, policy: CrisisPolicyRegistry) -> None:
        self._policy = policy

    def detect(self, turn: Turn) -> SafetyDetection:
        folded_text = turn.text.casefold()
        for signal in self._policy.signals:
            if any(phrase.casefold() in folded_text for phrase in signal.phrases):
                return SafetyDetection(
                    signal_id=signal.signal_id,
                    action=signal.action,
                    requires_override=signal.requires_override,
                    source_ids=signal.source_ids,
                )
        return SafetyDetection(
            signal_id=None,
            action=SafetyAction.CONTINUE_SUPPORT,
            requires_override=False,
            source_ids=(),
        )
