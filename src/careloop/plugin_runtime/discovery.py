"""Allowlisted local entry-point discovery with deterministic dependency order."""

from collections.abc import Iterable
from dataclasses import dataclass
from importlib import metadata
from typing import Protocol, cast

from careloop.agent_runtime import PluginManifestV1
from careloop.plugin_runtime.contracts import (
    PluginAllowlistEntry,
    PluginAllowlistV1,
)

PLUGIN_ENTRY_POINT_GROUP = "careloop.plugins.v1"


class PluginDiscoveryError(ValueError):
    """Raised when the local plugin set does not match the frozen allowlist."""


class EntryPointLike(Protocol):
    """Structural subset shared by importlib and deterministic test entries."""

    name: str
    value: str
    group: str

    def load(self) -> object: ...


@dataclass(frozen=True, slots=True)
class DiscoveredPluginCatalog:
    """Validated manifests in stable dependency-before-dependant order."""

    entry_point_names: tuple[str, ...]
    manifests: tuple[PluginManifestV1, ...]


def discover_allowlisted_plugins(
    allowlist: PluginAllowlistV1,
    *,
    entry_points: Iterable[EntryPointLike] | None = None,
) -> DiscoveredPluginCatalog:
    """Load exactly allowlisted local entry points and validate their manifests."""
    candidates = tuple(
        entry_points if entry_points is not None else _installed_entry_points()
    )
    selected = tuple(
        _select_candidate(entry, candidates) for entry in allowlist.entries
    )
    loaded = tuple(
        _load_manifest(entry, candidate)
        for entry, candidate in zip(allowlist.entries, selected, strict=True)
    )
    ordered_manifests = _dependency_order(loaded)
    entry_name_by_plugin_id = {
        entry.plugin_id: entry.entry_point_name for entry in allowlist.entries
    }
    return DiscoveredPluginCatalog(
        entry_point_names=tuple(
            entry_name_by_plugin_id[manifest.plugin_id]
            for manifest in ordered_manifests
        ),
        manifests=ordered_manifests,
    )


def _installed_entry_points() -> tuple[EntryPointLike, ...]:
    discovered = metadata.entry_points(group=PLUGIN_ENTRY_POINT_GROUP)
    return cast(tuple[EntryPointLike, ...], tuple(discovered))


def _select_candidate(
    allowed: PluginAllowlistEntry,
    candidates: tuple[EntryPointLike, ...],
) -> EntryPointLike:
    matches = tuple(
        candidate
        for candidate in candidates
        if candidate.group == PLUGIN_ENTRY_POINT_GROUP
        and candidate.name == allowed.entry_point_name
    )
    if len(matches) != 1 or matches[0].value != allowed.entry_point_value:
        raise PluginDiscoveryError(
            "allowlisted entry point "
            f"{allowed.entry_point_name!r} is missing or ambiguous"
        )
    return matches[0]


def _load_manifest(
    allowed: PluginAllowlistEntry,
    candidate: EntryPointLike,
) -> PluginManifestV1:
    try:
        factory = candidate.load()
        if not callable(factory):
            raise TypeError("entry point must load a manifest factory")
        manifest = PluginManifestV1.model_validate(factory())
    except Exception as error:
        raise PluginDiscoveryError(
            "allowlisted entry point "
            f"{allowed.entry_point_name!r} failed manifest validation"
        ) from error
    if (
        manifest.plugin_id != allowed.plugin_id
        or manifest.plugin_version != allowed.plugin_version
    ):
        raise PluginDiscoveryError(
            "manifest identity does not match allowlist for "
            f"{allowed.entry_point_name!r}"
        )
    return manifest


def _dependency_order(
    manifests: tuple[PluginManifestV1, ...],
) -> tuple[PluginManifestV1, ...]:
    by_id = {manifest.plugin_id: manifest for manifest in manifests}
    for manifest in manifests:
        missing = tuple(
            dependency
            for dependency in manifest.dependency_plugin_ids
            if dependency not in by_id
        )
        if missing:
            raise PluginDiscoveryError(
                f"plugin {manifest.plugin_id!r} has missing dependency {missing[0]!r}"
            )

    visiting: set[str] = set()
    visited: set[str] = set()
    ordered: list[PluginManifestV1] = []

    def visit(plugin_id: str) -> None:
        if plugin_id in visited:
            return
        if plugin_id in visiting:
            raise PluginDiscoveryError("plugin dependency cycle detected")
        visiting.add(plugin_id)
        manifest = by_id[plugin_id]
        for dependency in manifest.dependency_plugin_ids:
            visit(dependency)
        visiting.remove(plugin_id)
        visited.add(plugin_id)
        ordered.append(manifest)

    for manifest in manifests:
        visit(manifest.plugin_id)
    return tuple(ordered)
