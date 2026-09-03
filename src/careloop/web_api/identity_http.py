"""FastAPI request adapters for validated local or OIDC identities."""

from collections.abc import Callable
from datetime import datetime

from fastapi import Request

from careloop.web_api.identity import (
    IdentityContextV1,
    IdentityRole,
    LocalSyntheticIdentityAdapter,
    OidcIdentityAdapter,
)


class LocalRequestIdentity:
    """Map explicit development headers through the synthetic identity adapter."""

    def __init__(self, adapter: LocalSyntheticIdentityAdapter) -> None:
        self._adapter = adapter

    def __call__(self, request: Request) -> IdentityContextV1:
        subject = request.headers.get(
            "X-CareLoop-Demo-Subject", "synthetic-local:participant-1"
        )
        raw_role = request.headers.get("X-CareLoop-Demo-Role", "participant")
        try:
            role = IdentityRole(raw_role)
        except ValueError as error:
            raise PermissionError("unknown local synthetic role") from error
        return self._adapter.authenticate(subject=subject, role=role)


class OidcRequestIdentity:
    """Require a bearer token and request-bound nonce for the OIDC adapter."""

    def __init__(
        self,
        *,
        adapter: OidcIdentityAdapter,
        clock: Callable[[], datetime],
    ) -> None:
        self._adapter = adapter
        self._clock = clock

    def __call__(self, request: Request) -> IdentityContextV1:
        authorization = request.headers.get("Authorization", "")
        scheme, separator, token = authorization.partition(" ")
        nonce = request.headers.get("X-OIDC-Nonce", "")
        if scheme.casefold() != "bearer" or not separator or not token.strip():
            raise PermissionError("bearer token is required")
        return self._adapter.authenticate(
            token,
            expected_nonce=nonce,
            as_of=self._clock(),
        )
