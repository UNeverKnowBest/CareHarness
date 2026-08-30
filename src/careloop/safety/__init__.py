"""Synthetic-only fail-closed safety routing and ethical output policy."""

from careloop.safety.crisis_router import CrisisRouter
from careloop.safety.output_policy import EthicalOutputPolicy
from careloop.safety.registry import (
    CrisisPolicyRegistry,
    EthicalPolicyRegistry,
    load_crisis_policy,
    load_ethical_policy,
)
from careloop.safety.resource_registry import (
    ResourcePolicyRegistry,
    ResourceSelectionStatus,
    load_resource_registry,
)
from careloop.safety.runtime import (
    SafetyRuntimeResult,
    SafetyRuntimeStatus,
    SyntheticSafetyRuntime,
)
from careloop.safety.synthetic_detector import SyntheticSafetySignalDetector

__all__ = [
    "CrisisPolicyRegistry",
    "CrisisRouter",
    "EthicalOutputPolicy",
    "EthicalPolicyRegistry",
    "ResourcePolicyRegistry",
    "ResourceSelectionStatus",
    "SafetyRuntimeResult",
    "SafetyRuntimeStatus",
    "SyntheticSafetyRuntime",
    "SyntheticSafetySignalDetector",
    "load_crisis_policy",
    "load_ethical_policy",
    "load_resource_registry",
]
