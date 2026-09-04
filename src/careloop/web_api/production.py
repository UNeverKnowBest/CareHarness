"""Production-only OIDC composition for removable deployment adapters."""

import os
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, Self

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ConfigDict, SecretStr, model_validator

from careloop.agent_runtime.contracts import RuntimeContractModel
from careloop.durable_runtime import create_postgres_engine
from careloop.web_api.app import create_app
from careloop.web_api.demo_service import LocalResearchService
from careloop.web_api.identity import (
    OidcIdentityAdapter,
    OidcSettings,
    PyJwtTokenVerifier,
)
from careloop.web_api.identity_http import OidcRequestIdentity


class ProductionSettingsV1(RuntimeContractModel):
    """Explicit deployment settings that make local demo identity impossible."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    environment: Literal["production"]
    local_synthetic_identity_enabled: Literal[False]
    database_url: SecretStr
    web_origin: str
    oidc_issuer: str
    oidc_audience: str
    oidc_public_key: SecretStr
    oidc_algorithm: Literal["RS256", "ES256"]
    repository_root: Path

    @model_validator(mode="after")
    def validate_production_values(self) -> Self:
        if not self.web_origin.startswith("https://"):
            raise ValueError("web_origin must use HTTPS")
        if not self.oidc_issuer.startswith("https://"):
            raise ValueError("oidc_issuer must use HTTPS")
        if not self.oidc_audience.strip():
            raise ValueError("oidc_audience must not be blank")
        if not self.database_url.get_secret_value().strip():
            raise ValueError("database_url must not be blank")
        public_key = self.oidc_public_key.get_secret_value().strip()
        if not public_key:
            raise ValueError("oidc_public_key must not be blank")
        if "PRIVATE KEY" in public_key or not public_key.startswith(
            ("-----BEGIN PUBLIC KEY-----", "-----BEGIN CERTIFICATE-----")
        ):
            raise ValueError("oidc_public_key must contain only public PEM material")
        if not self.repository_root.is_dir():
            raise ValueError("repository_root must be an existing directory")
        return self


def production_settings_from_environment(
    environment: Mapping[str, str] | None = None,
) -> ProductionSettingsV1:
    """Load only explicit production values; no development fallback is allowed."""
    values = os.environ if environment is None else environment
    return ProductionSettingsV1.model_validate(
        {
            "environment": values["CARELOOP_ENVIRONMENT"],
            "local_synthetic_identity_enabled": values[
                "CARELOOP_ENABLE_LOCAL_SYNTHETIC_IDENTITY"
            ].casefold()
            == "true",
            "database_url": values["CARELOOP_DATABASE_URL"],
            "web_origin": values["CARELOOP_WEB_ORIGIN"],
            "oidc_issuer": values["CARELOOP_OIDC_ISSUER"],
            "oidc_audience": values["CARELOOP_OIDC_AUDIENCE"],
            "oidc_public_key": values["CARELOOP_OIDC_PUBLIC_KEY"],
            "oidc_algorithm": values["CARELOOP_OIDC_ALGORITHM"],
            "repository_root": Path(values["CARELOOP_REPOSITORY_ROOT"]),
        }
    )


def create_production_app(
    settings: ProductionSettingsV1,
    *,
    clock: Callable[[], datetime],
) -> FastAPI:
    """Compose OIDC and durable adapters without enabling synthetic demo identity."""
    validated = ProductionSettingsV1.model_validate(settings.model_dump())
    engine = create_postgres_engine(validated.database_url.get_secret_value())
    service = LocalResearchService(
        engine=engine,
        repository_root=validated.repository_root,
        clock=clock,
    )
    identity_adapter = OidcIdentityAdapter(
        settings=OidcSettings(
            issuer=validated.oidc_issuer,
            audience=validated.oidc_audience,
        ),
        verifier=PyJwtTokenVerifier(
            public_key=validated.oidc_public_key.get_secret_value(),
            algorithm=validated.oidc_algorithm,
        ),
    )
    app = create_app(
        service=service,
        identity_dependency=OidcRequestIdentity(adapter=identity_adapter, clock=clock),
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[validated.web_origin],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "Idempotency-Key",
            "Last-Event-ID",
            "X-OIDC-Nonce",
        ],
    )
    return app


def create_production_app_from_environment() -> FastAPI:
    """Uvicorn factory for cloud templates; credentials remain environment-injected."""
    return create_production_app(
        production_settings_from_environment(),
        clock=lambda: datetime.now(UTC),
    )
