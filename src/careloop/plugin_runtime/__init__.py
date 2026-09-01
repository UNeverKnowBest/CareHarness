"""Allowlisted local plugin discovery for the synthetic runtime."""

from careloop.plugin_runtime.contracts import (
    PluginAllowlistEntry,
    PluginAllowlistV1,
)
from careloop.plugin_runtime.discovery import (
    PLUGIN_ENTRY_POINT_GROUP,
    DiscoveredPluginCatalog,
    PluginDiscoveryError,
    discover_allowlisted_plugins,
)

__all__ = [
    "PLUGIN_ENTRY_POINT_GROUP",
    "DiscoveredPluginCatalog",
    "PluginAllowlistEntry",
    "PluginAllowlistV1",
    "PluginDiscoveryError",
    "discover_allowlisted_plugins",
]
