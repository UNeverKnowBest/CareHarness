import pytest
from pydantic import ValidationError

from careloop.agent_runtime import PluginKind
from careloop.durable_runtime import PluginProfileEntryV1, PluginProfileV1


def _entry(
    plugin_id: str,
    kind: PluginKind,
    *,
    enabled: bool = True,
    locked: bool = True,
) -> PluginProfileEntryV1:
    return PluginProfileEntryV1(
        contract_version="v1",
        plugin_id=plugin_id,
        plugin_version="1.0.0",
        kind=kind,
        enabled=enabled,
        locked=locked,
        configuration={},
    )


def test_profile_requires_every_safety_critical_kind_enabled_and_locked() -> None:
    profile = PluginProfileV1(
        contract_version="v1",
        profile_id="profile-safe-default",
        profile_version="1",
        plugins=(
            _entry("provider", PluginKind.MODEL_PROVIDER),
            _entry("input", PluginKind.INPUT_SAFETY_DETECTOR),
            _entry("output", PluginKind.OUTPUT_GUARD),
            _entry("resources", PluginKind.RESOURCE_CATALOG),
            _entry(
                "reporter",
                PluginKind.REPORTER,
                enabled=False,
                locked=False,
            ),
        ),
    )

    assert profile.plugins[-1].enabled is False
    assert all(item.locked for item in profile.plugins[:4])


@pytest.mark.parametrize("enabled", [True, False])
def test_critical_plugin_cannot_be_unlocked_or_disabled(enabled: bool) -> None:
    with pytest.raises(ValidationError, match="critical plugin"):
        _entry(
            "provider",
            PluginKind.MODEL_PROVIDER,
            enabled=enabled,
            locked=False,
        )


def test_profile_requires_unique_plugins_and_all_critical_kinds() -> None:
    provider = _entry("provider", PluginKind.MODEL_PROVIDER)

    with pytest.raises(ValidationError, match="unique"):
        PluginProfileV1(
            contract_version="v1",
            profile_id="profile-duplicate",
            profile_version="1",
            plugins=(provider, provider),
        )

    with pytest.raises(ValidationError, match="required critical plugin kinds"):
        PluginProfileV1(
            contract_version="v1",
            profile_id="profile-incomplete",
            profile_version="1",
            plugins=(provider,),
        )
