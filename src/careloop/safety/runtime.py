"""Synthetic runtime proving safety-before-response and output-before-visibility."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from typing import Protocol

from careloop.domain import CrisisResource, Finding, SafetyEvent, Turn
from careloop.safety.crisis_router import CrisisRouteDecision
from careloop.safety.output_policy import EthicalOutputDecision
from careloop.safety.registry import CrisisPolicyRegistry
from careloop.safety.resource_registry import ResourceSelectionStatus
from careloop.safety.synthetic_detector import SafetyDetection


class Detector(Protocol):
    def detect(self, turn: Turn) -> SafetyDetection: ...


class Router(Protocol):
    def route(
        self,
        turn: Turn,
        detection: SafetyDetection,
        *,
        jurisdiction: str | None,
        as_of: date,
    ) -> CrisisRouteDecision: ...


class OutputPolicy(Protocol):
    def evaluate(
        self, output: Turn, *, override_active: bool
    ) -> EthicalOutputDecision: ...


class SafetyRuntimeStatus(StrEnum):
    NORMAL_RESPONSE_ALLOWED = "NORMAL_RESPONSE_ALLOWED"
    CRISIS_OVERRIDE = "CRISIS_OVERRIDE"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"


@dataclass(frozen=True, slots=True)
class SafetyRuntimeResult:
    status: SafetyRuntimeStatus
    event: SafetyEvent | None
    resources: tuple[CrisisResource, ...]
    resource_status: ResourceSelectionStatus | None
    findings: tuple[Finding, ...]
    evaluated_output: Turn | None
    visible_output: Turn | None

    @property
    def human_review_required(self) -> bool:
        return self.status is SafetyRuntimeStatus.HUMAN_REVIEW_REQUIRED


class SyntheticSafetyRuntime:
    def __init__(
        self,
        policy: CrisisPolicyRegistry,
        *,
        detector: Detector,
        router: Router,
        output_policy: OutputPolicy,
    ) -> None:
        self._policy = policy
        self._detector = detector
        self._router = router
        self._output_policy = output_policy

    def _fail_closed(
        self,
        turn: Turn,
        *,
        findings: tuple[Finding, ...] = (),
        evaluated_output: Turn | None = None,
    ) -> SafetyRuntimeResult:
        source_ids = tuple(
            dict.fromkeys(
                self._policy.fail_closed_source_ids
                + tuple(source for finding in findings for source in finding.source_ids)
            )
        )
        event = SafetyEvent(
            event_id=f"{turn.turn_id}:fail-closed",
            triggering_turn_ids=(turn.turn_id,),
            action=self._policy.fail_closed_action,
            requires_override=True,
            normal_flow_suppressed=True,
            source_ids=source_ids,
            resource_ids=(),
            crisis_policy_version=self._policy.crisis_policy_version,
        )
        return SafetyRuntimeResult(
            status=SafetyRuntimeStatus.HUMAN_REVIEW_REQUIRED,
            event=event,
            resources=(),
            resource_status=None,
            findings=findings,
            evaluated_output=evaluated_output,
            visible_output=None,
        )

    def handle(
        self,
        turn: Turn,
        *,
        jurisdiction: str | None,
        as_of: date,
        responder: Callable[[Turn], str],
    ) -> SafetyRuntimeResult:
        routed_input = self.route_input(
            turn,
            jurisdiction=jurisdiction,
            as_of=as_of,
        )
        if routed_input is not None:
            return routed_input

        response_text = responder(turn)
        output = Turn(
            turn_id=f"{turn.turn_id}:assistant",
            sequence=turn.sequence + 1,
            role="assistant",
            text=response_text,
        )
        try:
            output_decision = self._output_policy.evaluate(
                output, override_active=False
            )
        except Exception:
            return self._fail_closed(turn, evaluated_output=output)
        if not output_decision.allowed:
            return self._fail_closed(
                turn,
                findings=output_decision.findings,
                evaluated_output=output,
            )
        return SafetyRuntimeResult(
            status=SafetyRuntimeStatus.NORMAL_RESPONSE_ALLOWED,
            event=None,
            resources=(),
            resource_status=None,
            findings=(),
            evaluated_output=output,
            visible_output=output,
        )

    def route_input(
        self,
        turn: Turn,
        *,
        jurisdiction: str | None,
        as_of: date,
    ) -> SafetyRuntimeResult | None:
        """Return override/failure evidence or None before any responder call."""
        try:
            detection = self._detector.detect(turn)
        except Exception:
            return self._fail_closed(turn)

        if detection.requires_override:
            try:
                routed = self._router.route(
                    turn,
                    detection,
                    jurisdiction=jurisdiction,
                    as_of=as_of,
                )
            except Exception:
                return self._fail_closed(turn)
            status = (
                SafetyRuntimeStatus.HUMAN_REVIEW_REQUIRED
                if routed.human_review_required
                else SafetyRuntimeStatus.CRISIS_OVERRIDE
            )
            return SafetyRuntimeResult(
                status=status,
                event=routed.event,
                resources=routed.resources,
                resource_status=routed.resource_status,
                findings=(),
                evaluated_output=None,
                visible_output=None,
            )
        return None
