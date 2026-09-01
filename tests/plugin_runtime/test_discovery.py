from collections.abc import Callable
from dataclasses import dataclass

import pytest
from pydantic import ValidationError

from careloop.agent_runtime import (
    PluginFailureMode,
    PluginKind,
    PluginManifestV1,
)
from careloop.plugin_runtime import (
    PLUGIN_ENTRY_POINT_GROUP,
    PluginAllowlistEntry,
    PluginAllowlistV1,
    PluginDiscoveryError,
    discover_allowlisted_plugins,
)


@dataclass
class FakeEntryPoint:
    name: str
    value: str
    target: Callable[[], PluginManifestV1]
    group: str = PLUGIN_ENTRY_POINT_GROUP
    load_count: int = 0

    def load(self) -> object:
        self.load_count += 1
        return self.target


def _manifest(
    plugin_id: str,
    *,
    version: str = "1.0.0",
    kind: PluginKind = PluginKind.OUTPUT_GUARD,
    dependencies: tuple[str, ...] = (),
) -> PluginManifestV1:
    return PluginManifestV1(
        plugin_api_version="v1",
        plugin_id=plugin_id,
        plugin_version=version,
        kind=kind,
        capabilities=(f"{plugin_id}-capability",),
        configuration_schema_id=f"{plugin_id}.config.v1",
        dependency_plugin_ids=dependencies,
        failure_mode=PluginFailureMode.CRITICAL_FAIL_CLOSED,
        default_enabled=True,
    )


def _allowlist(*entries: PluginAllowlistEntry) -> PluginAllowlistV1:
    return PluginAllowlistV1(contract_version="v1", entries=entries)


def _entry(
    name: str,
    value: str,
    plugin_id: str,
    version: str = "1.0.0",
) -> PluginAllowlistEntry:
    return PluginAllowlistEntry(
        entry_point_name=name,
        entry_point_value=value,
        plugin_id=plugin_id,
        plugin_version=version,
    )


def test_discovery_loads_only_exact_allowlisted_entry_points() -> None:
    approved = FakeEntryPoint(
        name="guard",
        value="synthetic_plugins:guard_manifest",
        target=lambda: _manifest("plugin-guard"),
    )
    unapproved = FakeEntryPoint(
        name="unapproved",
        value="untrusted:manifest",
        target=lambda: _manifest("plugin-unapproved"),
    )

    catalog = discover_allowlisted_plugins(
        _allowlist(
            _entry(
                "guard",
                "synthetic_plugins:guard_manifest",
                "plugin-guard",
            )
        ),
        entry_points=(unapproved, approved),
    )

    assert catalog.entry_point_names == ("guard",)
    assert tuple(item.plugin_id for item in catalog.manifests) == ("plugin-guard",)
    assert approved.load_count == 1
    assert unapproved.load_count == 0


@pytest.mark.parametrize(
    "entry_points",
    [
        (),
        (
            FakeEntryPoint(
                name="guard",
                value="wrong_module:manifest",
                target=lambda: _manifest("plugin-guard"),
            ),
        ),
    ],
)
def test_discovery_rejects_missing_or_value_mismatched_allowlisted_entry_point(
    entry_points: tuple[FakeEntryPoint, ...],
) -> None:
    allowlist = _allowlist(
        _entry("guard", "synthetic_plugins:guard_manifest", "plugin-guard")
    )

    with pytest.raises(PluginDiscoveryError, match="allowlisted entry point"):
        discover_allowlisted_plugins(allowlist, entry_points=entry_points)

    assert all(item.load_count == 0 for item in entry_points)


@pytest.mark.parametrize(
    ("actual_id", "actual_version"),
    [("plugin-other", "1.0.0"), ("plugin-guard", "2.0.0")],
)
def test_discovery_rejects_manifest_identity_or_version_mismatch(
    actual_id: str,
    actual_version: str,
) -> None:
    candidate = FakeEntryPoint(
        name="guard",
        value="synthetic_plugins:guard_manifest",
        target=lambda: _manifest(actual_id, version=actual_version),
    )

    with pytest.raises(PluginDiscoveryError, match="manifest identity"):
        discover_allowlisted_plugins(
            _allowlist(
                _entry(
                    "guard",
                    "synthetic_plugins:guard_manifest",
                    "plugin-guard",
                )
            ),
            entry_points=(candidate,),
        )


def test_discovery_orders_dependencies_before_dependants() -> None:
    provider = FakeEntryPoint(
        name="provider",
        value="synthetic_plugins:provider_manifest",
        target=lambda: _manifest(
            "plugin-provider",
            kind=PluginKind.MODEL_PROVIDER,
            dependencies=("plugin-guard",),
        ),
    )
    guard = FakeEntryPoint(
        name="guard",
        value="synthetic_plugins:guard_manifest",
        target=lambda: _manifest("plugin-guard"),
    )

    catalog = discover_allowlisted_plugins(
        _allowlist(
            _entry(
                "provider",
                "synthetic_plugins:provider_manifest",
                "plugin-provider",
            ),
            _entry(
                "guard",
                "synthetic_plugins:guard_manifest",
                "plugin-guard",
            ),
        ),
        entry_points=(provider, guard),
    )

    assert tuple(item.plugin_id for item in catalog.manifests) == (
        "plugin-guard",
        "plugin-provider",
    )


@pytest.mark.parametrize("cycle", [False, True])
def test_discovery_rejects_missing_dependencies_and_cycles(cycle: bool) -> None:
    first_dependencies = ("plugin-second",)
    second_dependencies = ("plugin-first",) if cycle else ("plugin-missing",)
    first = FakeEntryPoint(
        name="first",
        value="synthetic_plugins:first_manifest",
        target=lambda: _manifest("plugin-first", dependencies=first_dependencies),
    )
    second = FakeEntryPoint(
        name="second",
        value="synthetic_plugins:second_manifest",
        target=lambda: _manifest("plugin-second", dependencies=second_dependencies),
    )

    with pytest.raises(PluginDiscoveryError, match="dependency"):
        discover_allowlisted_plugins(
            _allowlist(
                _entry("first", "synthetic_plugins:first_manifest", "plugin-first"),
                _entry(
                    "second",
                    "synthetic_plugins:second_manifest",
                    "plugin-second",
                ),
            ),
            entry_points=(first, second),
        )


def test_allowlist_is_strict_versioned_and_has_unique_identities() -> None:
    entry = _entry("guard", "synthetic_plugins:guard_manifest", "plugin-guard")

    with pytest.raises(ValidationError, match="contract_version"):
        PluginAllowlistV1(contract_version="v2", entries=(entry,))
    with pytest.raises(ValidationError, match="entries"):
        PluginAllowlistV1(contract_version="v1", entries=(entry, entry))
    with pytest.raises(ValidationError, match="unexpected"):
        PluginAllowlistV1.model_validate(
            {"contract_version": "v1", "entries": [entry], "unexpected": True}
        )
