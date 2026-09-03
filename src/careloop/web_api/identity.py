"""OIDC claim validation and development-only synthetic identity adapters."""

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal, Protocol

import jwt

from careloop.agent_runtime.contracts import (
    ContractVersion,
    NonBlankStr,
    RuntimeContractModel,
)


class IdentityRole(StrEnum):
    """Exact server-authorized research roles."""

    PARTICIPANT = "participant"
    REVIEWER = "reviewer"
    ADMIN = "admin"


class IdentityContextV1(RuntimeContractModel):
    """Validated request identity with no raw credential."""

    contract_version: ContractVersion
    subject: NonBlankStr
    role: IdentityRole
    auth_source: Literal["oidc", "local_synthetic"]


class VerifiedOidcTokenV1(RuntimeContractModel):
    """Claims returned only after an injected verifier checks the signature."""

    contract_version: ContractVersion
    signature_verified: Literal[True]
    issuer: NonBlankStr
    audiences: tuple[NonBlankStr, ...]
    subject: NonBlankStr
    expires_at: int
    nonce: NonBlankStr
    role: IdentityRole


class OidcSettings(RuntimeContractModel):
    issuer: NonBlankStr
    audience: NonBlankStr


class OidcTokenVerifier(Protocol):
    """Cryptographic verifier boundary supplied by the deployment."""

    def verify(self, raw_token: str) -> VerifiedOidcTokenV1: ...


class PyJwtTokenVerifier:
    """Verify one asymmetric JWT using deployment-injected trusted key material."""

    def __init__(
        self,
        *,
        public_key: Any,
        algorithm: Literal["RS256", "ES256"],
    ) -> None:
        self._public_key = public_key
        self._algorithm = algorithm

    def verify(self, raw_token: str) -> VerifiedOidcTokenV1:
        try:
            claims = jwt.decode(
                raw_token,
                self._public_key,
                algorithms=[self._algorithm],
                options={
                    "verify_aud": False,
                    "verify_exp": False,
                    "require": [
                        "iss",
                        "aud",
                        "sub",
                        "exp",
                        "nonce",
                        "careloop_role",
                    ],
                },
            )
            raw_audience = claims["aud"]
            audiences = (
                (raw_audience,)
                if isinstance(raw_audience, str)
                else tuple(raw_audience)
            )
            return VerifiedOidcTokenV1(
                contract_version="v1",
                signature_verified=True,
                issuer=claims["iss"],
                audiences=audiences,
                subject=claims["sub"],
                expires_at=claims["exp"],
                nonce=claims["nonce"],
                role=claims["careloop_role"],
            )
        except (jwt.PyJWTError, KeyError, TypeError, ValueError) as error:
            raise PermissionError("OIDC signature or claims are invalid") from error


class OidcIdentityAdapter:
    """Validate signed claims against configured server-side expectations."""

    def __init__(self, *, settings: OidcSettings, verifier: OidcTokenVerifier) -> None:
        self._settings = settings
        self._verifier = verifier

    def authenticate(
        self,
        raw_token: str,
        *,
        expected_nonce: str,
        as_of: datetime,
    ) -> IdentityContextV1:
        if not raw_token.strip() or not expected_nonce.strip():
            raise PermissionError("OIDC token and nonce are required")
        if as_of.tzinfo is None or as_of.utcoffset() is None:
            raise ValueError("as_of must be timezone-aware")
        claims = VerifiedOidcTokenV1.model_validate(
            self._verifier.verify(raw_token).model_dump()
        )
        if claims.issuer != self._settings.issuer:
            raise PermissionError("OIDC issuer is not authorized")
        if self._settings.audience not in claims.audiences:
            raise PermissionError("OIDC audience is not authorized")
        if claims.expires_at <= int(as_of.timestamp()):
            raise PermissionError("OIDC token is expired")
        if claims.nonce != expected_nonce:
            raise PermissionError("OIDC nonce does not match")
        return IdentityContextV1(
            contract_version="v1",
            subject=claims.subject,
            role=claims.role,
            auth_source="oidc",
        )


class LocalIdentitySettings(RuntimeContractModel):
    environment: Literal["development", "production"]


class LocalSyntheticIdentityAdapter:
    """Explicit development identity that cannot start in production."""

    def __init__(self, settings: LocalIdentitySettings) -> None:
        if settings.environment == "production":
            raise RuntimeError("local synthetic identity is forbidden in production")

    def authenticate(
        self,
        *,
        subject: str,
        role: IdentityRole,
    ) -> IdentityContextV1:
        if not subject.startswith("synthetic-local:"):
            raise PermissionError("local identity must be explicitly synthetic")
        return IdentityContextV1(
            contract_version="v1",
            subject=subject,
            role=role,
            auth_source="local_synthetic",
        )


def require_role(identity: IdentityContextV1, *allowed: IdentityRole) -> None:
    """Deny access unless the server-mapped role is explicitly allowed."""
    if identity.role not in allowed:
        raise PermissionError("role is not authorized for this operation")
