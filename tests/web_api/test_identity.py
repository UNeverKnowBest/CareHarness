from datetime import UTC, datetime

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from pydantic import ValidationError

from careloop.web_api.identity import (
    IdentityRole,
    LocalIdentitySettings,
    LocalSyntheticIdentityAdapter,
    OidcIdentityAdapter,
    OidcSettings,
    PyJwtTokenVerifier,
    VerifiedOidcTokenV1,
    require_role,
)


class StubVerifier:
    def __init__(self, token: VerifiedOidcTokenV1) -> None:
        self.token = token
        self.received: list[str] = []

    def verify(self, raw_token: str) -> VerifiedOidcTokenV1:
        self.received.append(raw_token)
        return self.token


def _verified_token(**updates: object) -> VerifiedOidcTokenV1:
    values: dict[str, object] = {
        "contract_version": "v1",
        "signature_verified": True,
        "issuer": "https://identity.example.invalid",
        "audiences": ("careloop-research",),
        "subject": "researcher-1",
        "expires_at": 2_000_000_000,
        "nonce": "nonce-1",
        "role": IdentityRole.REVIEWER,
    }
    values.update(updates)
    return VerifiedOidcTokenV1.model_validate(values)


def test_oidc_adapter_validates_verified_claims_and_maps_exact_role() -> None:
    verifier = StubVerifier(_verified_token())
    adapter = OidcIdentityAdapter(
        settings=OidcSettings(
            issuer="https://identity.example.invalid",
            audience="careloop-research",
        ),
        verifier=verifier,
    )

    identity = adapter.authenticate(
        "signed-token",
        expected_nonce="nonce-1",
        as_of=datetime.fromtimestamp(1_900_000_000, tz=UTC),
    )

    assert identity.subject == "researcher-1"
    assert identity.role is IdentityRole.REVIEWER
    assert verifier.received == ["signed-token"]


@pytest.mark.parametrize(
    "token",
    [
        _verified_token(issuer="https://wrong.example.invalid"),
        _verified_token(audiences=("another-service",)),
        _verified_token(expires_at=1_800_000_000),
        _verified_token(nonce="wrong"),
    ],
)
def test_oidc_adapter_denies_invalid_issuer_audience_expiry_or_nonce(
    token: VerifiedOidcTokenV1,
) -> None:
    adapter = OidcIdentityAdapter(
        settings=OidcSettings(
            issuer="https://identity.example.invalid",
            audience="careloop-research",
        ),
        verifier=StubVerifier(token),
    )

    with pytest.raises(PermissionError):
        adapter.authenticate(
            "signed-token",
            expected_nonce="nonce-1",
            as_of=datetime.fromtimestamp(1_900_000_000, tz=UTC),
        )


def test_verified_token_cannot_claim_an_unverified_signature() -> None:
    with pytest.raises(ValidationError):
        _verified_token(signature_verified=False)


def test_local_synthetic_identity_is_development_only() -> None:
    adapter = LocalSyntheticIdentityAdapter(
        LocalIdentitySettings(environment="development")
    )
    identity = adapter.authenticate(
        subject="synthetic-local:participant-1",
        role=IdentityRole.PARTICIPANT,
    )
    assert identity.auth_source == "local_synthetic"

    with pytest.raises(RuntimeError, match="production"):
        LocalSyntheticIdentityAdapter(LocalIdentitySettings(environment="production"))


def test_role_authorization_denies_by_default() -> None:
    adapter = LocalSyntheticIdentityAdapter(
        LocalIdentitySettings(environment="development")
    )
    participant = adapter.authenticate(
        subject="synthetic-local:participant-1",
        role=IdentityRole.PARTICIPANT,
    )

    require_role(participant, IdentityRole.PARTICIPANT)
    with pytest.raises(PermissionError):
        require_role(participant, IdentityRole.REVIEWER)


def test_pyjwt_verifier_accepts_only_a_valid_asymmetric_signature() -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    claims = {
        "iss": "https://identity.example.invalid",
        "aud": "careloop-research",
        "sub": "researcher-1",
        "exp": 2_000_000_000,
        "nonce": "nonce-1",
        "careloop_role": "reviewer",
    }
    token = jwt.encode(claims, private_key, algorithm="RS256")
    verifier = PyJwtTokenVerifier(public_key=public_key, algorithm="RS256")

    verified = verifier.verify(token)

    assert verified.signature_verified is True
    assert verified.role is IdentityRole.REVIEWER
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    invalid = jwt.encode(claims, other_key, algorithm="RS256")
    with pytest.raises(PermissionError):
        verifier.verify(invalid)
