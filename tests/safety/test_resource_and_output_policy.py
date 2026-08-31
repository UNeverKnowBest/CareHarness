import json
from dataclasses import fields
from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from careloop.domain import Turn
from careloop.safety import (
    CrisisPolicyRegistry,
    EthicalOutputPolicy,
    EthicalPolicyRegistry,
    ResourcePolicyRegistry,
    ResourceSelectionStatus,
    SafetyRuntimeResult,
    load_crisis_policy,
    load_ethical_policy,
    load_resource_registry,
)

ROOT = Path(__file__).parents[2]
POLICY_ROOT = ROOT / "policies"
AS_OF = date(2026, 8, 29)


def _assistant_turn(text: str) -> Turn:
    return Turn(
        turn_id="synthetic-assistant-t1", sequence=1, role="assistant", text=text
    )


def test_policy_registries_freeze_versions_rule_sources_and_order() -> None:
    crisis = load_crisis_policy(POLICY_ROOT / "crisis.v1.json")
    ethical = load_ethical_policy(POLICY_ROOT / "ethical.v1.json")
    resources = load_resource_registry(POLICY_ROOT / "resources.v1.json")

    assert crisis.crisis_policy_version == "v1"
    assert ethical.ethical_policy_version == "v1"
    assert resources.resource_registry_version == "v1"
    assert tuple(signal.signal_id for signal in crisis.signals) == (
        "ambiguous_current",
        "historical_context",
        "third_party_context",
        "quoted_context",
        "current_plan",
        "current_preparation",
        "already_acted",
    )
    assert tuple(rule.rule_id for rule in ethical.rules) == (
        "ethical.role_impersonation",
        "ethical.diagnosis_claim",
        "ethical.medication_advice",
        "ethical.coercion",
        "ethical.invalidation",
        "ethical.over_reassurance",
        "ethical.dependency",
        "ethical.confidentiality_claim",
        "ethical.clinical_overclaim",
        "ethical.crisis_flow_continuation",
    )


def test_resource_selection_is_exact_source_linked_and_replayable_at_as_of() -> None:
    registry = load_resource_registry(POLICY_ROOT / "resources.v1.json")

    first = registry.select(jurisdiction="ZZ-TEST", as_of=AS_OF)
    second = registry.select(jurisdiction="ZZ-TEST", as_of=AS_OF)

    assert first == second
    assert first.status is ResourceSelectionStatus.SELECTED
    assert first.resource is not None
    assert first.resource.resource_id == "synthetic-human-help-zz-test"
    assert first.resource.jurisdiction == "ZZ-TEST"
    assert first.resource.resource_registry_version == "v1"
    assert first.resource.source_url.endswith("zz-test-v1")
    assert first.resource.verified_on <= AS_OF <= first.resource.expires_on


def test_resource_selection_never_guesses_missing_wrong_or_stale_locale() -> None:
    registry = load_resource_registry(POLICY_ROOT / "resources.v1.json")

    missing = registry.select(jurisdiction=None, as_of=AS_OF)
    blank = registry.select(jurisdiction="  ", as_of=AS_OF)
    wrong = registry.select(jurisdiction="ZZ-MISSING", as_of=AS_OF)
    stale = registry.select(jurisdiction="ZZ-STALE", as_of=AS_OF)

    assert missing.status is ResourceSelectionStatus.MISSING_JURISDICTION
    assert blank.status is ResourceSelectionStatus.MISSING_JURISDICTION
    assert wrong.status is ResourceSelectionStatus.JURISDICTION_MISMATCH
    assert stale.status is ResourceSelectionStatus.OUTSIDE_AS_OF
    assert all(decision.resource is None for decision in (missing, blank, wrong, stale))


@pytest.mark.parametrize(
    ("mutation", "match"),
    (
        ("unknown-version", "resource_registry_version"),
        ("not-allowlisted", "is_allowlisted"),
        ("unregistered-source", "source_url"),
    ),
)
def test_resource_registry_rejects_unknown_version_nonallowlist_and_source(
    tmp_path: Path, mutation: str, match: str
) -> None:
    raw = json.loads((POLICY_ROOT / "resources.v1.json").read_text(encoding="utf-8"))
    if mutation == "unknown-version":
        raw["resource_registry_version"] = "v2"
    elif mutation == "not-allowlisted":
        raw["resources"][0]["is_allowlisted"] = False
    else:
        raw["resources"][0]["source_url"] = "https://unregistered.invalid/resource"
    path = tmp_path / f"{mutation}.json"
    path.write_text(json.dumps(raw), encoding="utf-8")

    with pytest.raises(ValidationError, match=match):
        load_resource_registry(path)


@pytest.mark.parametrize(
    ("phrase", "rule_id", "override_active"),
    (
        (
            "[SYNTHETIC OUTPUT VIOLATION: ROLE IMPERSONATION]",
            "ethical.role_impersonation",
            False,
        ),
        (
            "[SYNTHETIC OUTPUT VIOLATION: DIAGNOSIS]",
            "ethical.diagnosis_claim",
            False,
        ),
        (
            "[SYNTHETIC OUTPUT VIOLATION: MEDICATION ADVICE]",
            "ethical.medication_advice",
            False,
        ),
        (
            "[SYNTHETIC OUTPUT VIOLATION: COERCION]",
            "ethical.coercion",
            False,
        ),
        (
            "[SYNTHETIC OUTPUT VIOLATION: INVALIDATION]",
            "ethical.invalidation",
            False,
        ),
        ("You are safe", "ethical.over_reassurance", False),
        (
            "[SYNTHETIC OUTPUT VIOLATION: DEPENDENCY]",
            "ethical.dependency",
            False,
        ),
        (
            "[SYNTHETIC OUTPUT VIOLATION: CONFIDENTIALITY]",
            "ethical.confidentiality_claim",
            False,
        ),
        (
            "This system guarantees real-world safety",
            "ethical.clinical_overclaim",
            False,
        ),
        (
            "Let us continue the ordinary CBT exercise",
            "ethical.crisis_flow_continuation",
            True,
        ),
    ),
)
def test_each_ethical_output_category_is_blocked_before_visibility(
    phrase: str, rule_id: str, override_active: bool
) -> None:
    policy = EthicalOutputPolicy(load_ethical_policy(POLICY_ROOT / "ethical.v1.json"))

    decision = policy.evaluate(
        _assistant_turn(f"[SYNTHETIC] {phrase}."),
        override_active=override_active,
    )

    assert decision.allowed is False
    assert tuple(finding.rule_id for finding in decision.findings) == (rule_id,)
    assert decision.findings[0].turn_ids == ("synthetic-assistant-t1",)
    assert decision.findings[0].source_ids
    assert decision.findings[0].evaluator_version == "v1"


def test_crisis_flow_continuation_rule_only_applies_during_override() -> None:
    policy = EthicalOutputPolicy(load_ethical_policy(POLICY_ROOT / "ethical.v1.json"))
    output = _assistant_turn("[SYNTHETIC] Let us continue the ordinary CBT exercise.")

    normal = policy.evaluate(output, override_active=False)
    override = policy.evaluate(output, override_active=True)

    assert normal.allowed is True
    assert normal.findings == ()
    assert override.allowed is False
    assert override.findings[0].rule_id == "ethical.crisis_flow_continuation"


def test_single_denial_cannot_release_an_unfounded_you_are_safe_statement() -> None:
    policy = EthicalOutputPolicy(load_ethical_policy(POLICY_ROOT / "ethical.v1.json"))
    output = _assistant_turn(
        "[SYNTHETIC] After one fictional denial, you are safe and no check is needed."
    )

    decision = policy.evaluate(output, override_active=False)

    assert decision.allowed is False
    assert decision.findings[0].rule_id == "ethical.over_reassurance"


def test_safe_output_has_no_findings_and_unknown_policy_versions_fail(
    tmp_path: Path,
) -> None:
    policy = EthicalOutputPolicy(load_ethical_policy(POLICY_ROOT / "ethical.v1.json"))
    decision = policy.evaluate(
        _assistant_turn("[SYNTHETIC] Choice-respecting fictional support."),
        override_active=False,
    )
    assert decision.allowed is True
    assert decision.findings == ()

    for filename, field in (
        ("crisis.v1.json", "crisis_policy_version"),
        ("ethical.v1.json", "ethical_policy_version"),
    ):
        raw = (POLICY_ROOT / filename).read_text(encoding="utf-8")
        path = tmp_path / filename
        path.write_text(
            raw.replace(f'"{field}": "v1"', f'"{field}": "v2"'),
            encoding="utf-8",
        )
        loader = (
            load_crisis_policy if filename.startswith("crisis") else load_ethical_policy
        )
        with pytest.raises(ValidationError, match=field):
            loader(path)


def test_safety_api_contains_no_risk_or_clinical_disposition_fields() -> None:
    prohibited = {
        "risk_score",
        "risk_level",
        "suicide_probability",
        "diagnosis",
        "clinical_disposition",
    }
    pydantic_fields = (
        set(CrisisPolicyRegistry.model_fields)
        | set(EthicalPolicyRegistry.model_fields)
        | set(ResourcePolicyRegistry.model_fields)
    )
    result_fields = {field.name for field in fields(SafetyRuntimeResult)}

    assert pydantic_fields.isdisjoint(prohibited)
    assert result_fields.isdisjoint(prohibited)
