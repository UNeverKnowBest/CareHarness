"""Typed crisis override routing and fail-closed resource handling."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

from careloop.domain import CrisisResource, SafetyAction, SafetyEvent, Turn
from careloop.safety.registry import CrisisPolicyRegistry
from careloop.safety.resource_registry import (
    ResourcePolicyRegistry,
    ResourceSelectionStatus,
)
from careloop.safety.synthetic_detector import SafetyDetection


def _ordered_unique(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


@dataclass(frozen=True, slots=True)
class CrisisRouteDecision:
    event: SafetyEvent
    resources: tuple[CrisisResource, ...]
    resource_status: ResourceSelectionStatus | None
    human_review_required: bool


class CrisisRouter:
    def __init__(
        self,
        policy: CrisisPolicyRegistry,
        resource_loader: Callable[[], ResourcePolicyRegistry],
    ) -> None:
        self._policy = policy
        self._resource_loader = resource_loader

    def route(
        self,
        turn: Turn,
        detection: SafetyDetection,
        *,
        jurisdiction: str | None,
        as_of: date,
    ) -> CrisisRouteDecision:
        if not detection.requires_override:
            raise ValueError("CrisisRouter requires an override detection")

        resources: tuple[CrisisResource, ...] = ()
        resource_ids: tuple[str, ...] = ()
        resource_status: ResourceSelectionStatus | None = None
        human_review_required = False
        source_ids = detection.source_ids

        if detection.action is SafetyAction.SEEK_EMERGENCY_HELP_NOW:
            try:
                registry = self._resource_loader()
                selection = registry.select(jurisdiction=jurisdiction, as_of=as_of)
                resource_status = selection.status
                if selection.resource is None:
                    human_review_required = True
                    source_ids = _ordered_unique(
                        source_ids + self._policy.fail_closed_source_ids
                    )
                else:
                    resources = (selection.resource,)
                    resource_ids = (selection.resource.resource_id,)
            except Exception:
                resource_status = ResourceSelectionStatus.LOADER_FAILURE
                human_review_required = True
                source_ids = _ordered_unique(
                    source_ids + self._policy.fail_closed_source_ids
                )

        event = SafetyEvent(
            event_id=f"{turn.turn_id}:crisis-override",
            triggering_turn_ids=(turn.turn_id,),
            action=detection.action,
            requires_override=True,
            normal_flow_suppressed=True,
            source_ids=source_ids,
            resource_ids=resource_ids,
            crisis_policy_version=self._policy.crisis_policy_version,
        )
        return CrisisRouteDecision(
            event=event,
            resources=resources,
            resource_status=resource_status,
            human_review_required=human_review_required,
        )
