from pathlib import Path

import pytest
from pydantic import ValidationError

from careloop.web_api.production import (
    ProductionSettingsV1,
    production_settings_from_environment,
)

PUBLIC_KEY = (
    "-----BEGIN PUBLIC KEY-----\ntest-only-placeholder\n-----END PUBLIC KEY-----"
)


def _settings(**updates: object) -> dict[str, object]:
    values: dict[str, object] = {
        "environment": "production",
        "local_synthetic_identity_enabled": False,
        "database_url": "postgresql+psycopg://service@/careloop",
        "web_origin": "https://research.example.invalid",
        "oidc_issuer": "https://identity.example.invalid",
        "oidc_audience": "careloop-research",
        "oidc_public_key": PUBLIC_KEY,
        "oidc_algorithm": "RS256",
        "repository_root": Path(__file__).parents[2],
    }
    values.update(updates)
    return values


def test_production_settings_reject_local_identity_or_nonproduction_mode() -> None:
    with pytest.raises(ValidationError):
        ProductionSettingsV1.model_validate(
            _settings(local_synthetic_identity_enabled=True)
        )
    with pytest.raises(ValidationError):
        ProductionSettingsV1.model_validate(_settings(environment="development"))
    with pytest.raises(ValidationError):
        ProductionSettingsV1.model_validate(_settings(web_origin="http://localhost"))
    with pytest.raises(ValidationError):
        ProductionSettingsV1.model_validate(_settings(oidc_public_key="   "))
    with pytest.raises(ValidationError):
        ProductionSettingsV1.model_validate(
            _settings(
                oidc_public_key=(
                    "-----BEGIN PRIVATE KEY-----\nforbidden\n-----END PRIVATE KEY-----"
                )
            )
        )


def test_production_settings_contain_no_private_oidc_key_or_provider_secret() -> None:
    settings = ProductionSettingsV1.model_validate(_settings())
    assert set(ProductionSettingsV1.model_fields) == {
        "environment",
        "local_synthetic_identity_enabled",
        "database_url",
        "web_origin",
        "oidc_issuer",
        "oidc_audience",
        "oidc_public_key",
        "oidc_algorithm",
        "repository_root",
    }
    assert "PRIVATE KEY" not in settings.oidc_public_key.get_secret_value()


def test_production_environment_loader_requires_explicit_oidc_and_disables_demo() -> (
    None
):
    settings = production_settings_from_environment(
        {
            "CARELOOP_ENVIRONMENT": "production",
            "CARELOOP_ENABLE_LOCAL_SYNTHETIC_IDENTITY": "false",
            "CARELOOP_DATABASE_URL": "postgresql+psycopg://service@/careloop",
            "CARELOOP_WEB_ORIGIN": "https://research.example.invalid",
            "CARELOOP_OIDC_ISSUER": "https://identity.example.invalid",
            "CARELOOP_OIDC_AUDIENCE": "careloop-research",
            "CARELOOP_OIDC_PUBLIC_KEY": PUBLIC_KEY,
            "CARELOOP_OIDC_ALGORITHM": "RS256",
            "CARELOOP_REPOSITORY_ROOT": str(Path(__file__).parents[2]),
        }
    )
    assert settings.environment == "production"
    assert settings.local_synthetic_identity_enabled is False

    with pytest.raises((KeyError, ValidationError)):
        production_settings_from_environment(
            {
                "CARELOOP_ENVIRONMENT": "production",
                "CARELOOP_ENABLE_LOCAL_SYNTHETIC_IDENTITY": "false",
            }
        )
