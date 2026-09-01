"""Strict allowlist contracts for removable runtime plugins."""

from typing import Annotated, Literal, Self

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator


def _non_blank(value: str) -> str:
    if not value.strip():
        raise ValueError("must not be empty or whitespace")
    return value


NonBlankStr = Annotated[str, AfterValidator(_non_blank)]


class PluginRuntimeContractModel(BaseModel):
    """Strict base for the M9 plugin-discovery contract."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class PluginAllowlistEntry(PluginRuntimeContractModel):
    """One exact entry-point and plugin identity approved for loading."""

    entry_point_name: NonBlankStr
    entry_point_value: NonBlankStr
    plugin_id: NonBlankStr
    plugin_version: NonBlankStr


class PluginAllowlistV1(PluginRuntimeContractModel):
    """Versioned closed set of Python entry points approved for discovery."""

    contract_version: Literal["v1"]
    entries: Annotated[tuple[PluginAllowlistEntry, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def validate_unique_identities(self) -> Self:
        entry_point_names = tuple(item.entry_point_name for item in self.entries)
        plugin_ids = tuple(item.plugin_id for item in self.entries)
        if len(set(entry_point_names)) != len(entry_point_names):
            raise ValueError("entries must contain unique entry_point_name values")
        if len(set(plugin_ids)) != len(plugin_ids):
            raise ValueError("entries must contain unique plugin_id values")
        return self
