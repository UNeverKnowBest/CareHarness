"""Explicit development-only Uvicorn entry point for Docker Compose."""

import os
from datetime import UTC, datetime
from pathlib import Path

from fastapi.middleware.cors import CORSMiddleware

from careloop.durable_runtime import create_postgres_engine
from careloop.web_api.app import create_app
from careloop.web_api.demo_service import LocalResearchService
from careloop.web_api.identity import (
    LocalIdentitySettings,
    LocalSyntheticIdentityAdapter,
)
from careloop.web_api.identity_http import LocalRequestIdentity

environment = os.getenv("CARELOOP_ENVIRONMENT", "production")
local_enabled = os.getenv("CARELOOP_ENABLE_LOCAL_SYNTHETIC_IDENTITY", "false")
if local_enabled.casefold() != "true":
    raise RuntimeError(
        "this Compose entry point requires explicit local synthetic identity enablement"
    )

identity_adapter = LocalSyntheticIdentityAdapter(
    LocalIdentitySettings.model_validate({"environment": environment})
)
database_url = os.environ["CARELOOP_DATABASE_URL"]
engine = create_postgres_engine(database_url)
service = LocalResearchService(
    engine=engine,
    repository_root=Path(__file__).parents[3],
    clock=lambda: datetime.now(UTC),
)
app = create_app(
    service=service,
    identity_dependency=LocalRequestIdentity(identity_adapter),
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("CARELOOP_WEB_ORIGIN", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Idempotency-Key",
        "Last-Event-ID",
        "X-CareLoop-Demo-Role",
        "X-CareLoop-Demo-Subject",
        "X-OIDC-Nonce",
    ],
)
