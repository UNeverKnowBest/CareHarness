"""Public M8 contracts for the synthetic CareLoop agent runtime."""

from careloop.agent_runtime.contracts import (
    MAX_DRAFT_REWRITE_ATTEMPTS,
    ArtifactProvenance,
    DraftDecision,
    DraftGateResult,
    ModelDraft,
    ModelRequest,
    PluginFailureMode,
    PluginKind,
    PluginManifestV1,
    PluginVersionRef,
    ReviewDecision,
    SafetyDisposition,
    SessionConfig,
    SessionState,
)
from careloop.agent_runtime.ports import ModelPort
from careloop.agent_runtime.state_machine import (
    InvalidSessionTransition,
    RuntimeEvent,
    SessionEvent,
    transition_session,
)

__all__ = [
    "MAX_DRAFT_REWRITE_ATTEMPTS",
    "ArtifactProvenance",
    "DraftDecision",
    "DraftGateResult",
    "InvalidSessionTransition",
    "ModelDraft",
    "ModelPort",
    "ModelRequest",
    "PluginFailureMode",
    "PluginKind",
    "PluginManifestV1",
    "PluginVersionRef",
    "ReviewDecision",
    "RuntimeEvent",
    "SafetyDisposition",
    "SessionConfig",
    "SessionEvent",
    "SessionState",
    "transition_session",
]
