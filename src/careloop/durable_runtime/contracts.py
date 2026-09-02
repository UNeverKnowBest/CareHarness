"""Strict M14 contracts for immutable plugin profiles and outbox evidence."""

from typing import Self

from pydantic import JsonValue, model_validator

from careloop.agent_runtime import PluginKind
from careloop.agent_runtime.contracts import (
    ContractVersion,
    NonBlankStr,
    RuntimeContractModel,
)

_CRITICAL_PLUGIN_KINDS = frozenset(
    {
        PluginKind.MODEL_PROVIDER,
        PluginKind.INPUT_SAFETY_DETECTOR,
        PluginKind.OUTPUT_GUARD,
        PluginKind.RESOURCE_CATALOG,
    }
)


class PluginProfileEntryV1(RuntimeContractModel):
    """One exact preinstalled plugin selection in an immutable profile."""

    contract_version: ContractVersion
    plugin_id: NonBlankStr
    plugin_version: NonBlankStr
    kind: PluginKind
    enabled: bool
    locked: bool
    configuration: dict[str, JsonValue]

    @model_validator(mode="after")
    def validate_critical_plugin_state(self) -> Self:
        if self.kind in _CRITICAL_PLUGIN_KINDS and not (self.enabled and self.locked):
            raise ValueError("critical plugin must be enabled and locked")
        return self


class PluginProfileV1(RuntimeContractModel):
    """A complete session-time plugin snapshot with locked safety dependencies."""

    contract_version: ContractVersion
    profile_id: NonBlankStr
    profile_version: NonBlankStr
    plugins: tuple[PluginProfileEntryV1, ...]

    @model_validator(mode="after")
    def validate_complete_unique_profile(self) -> Self:
        plugin_ids = tuple(item.plugin_id for item in self.plugins)
        if len(plugin_ids) != len(set(plugin_ids)):
            raise ValueError("plugins must contain unique plugin_id values")
        enabled_kinds = {
            item.kind for item in self.plugins if item.enabled and item.locked
        }
        missing = _CRITICAL_PLUGIN_KINDS - enabled_kinds
        if missing:
            values = ", ".join(sorted(item.value for item in missing))
            raise ValueError(f"required critical plugin kinds are missing: {values}")
        return self


class RuntimeOutboxRecord(RuntimeContractModel):
    """One committed event notification waiting for best-effort Redis delivery."""

    contract_version: ContractVersion
    outbox_id: int
    session_id: NonBlankStr
    event_id: NonBlankStr
    sequence: int
    payload: dict[str, JsonValue]
