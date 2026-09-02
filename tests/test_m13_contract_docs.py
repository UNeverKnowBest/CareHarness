import json
from pathlib import Path

ROOT = Path(__file__).parents[1]


def _normalized(path: str) -> str:
    return " ".join((ROOT / path).read_text(encoding="utf-8").split())


def test_m13_research_boundary_is_frozen_across_normative_documents() -> None:
    agents = _normalized("AGENTS.md")
    spec = _normalized("SPEC.md")
    architecture = _normalized("ARCHITECTURE.md")
    plan = _normalized("PLAN.md")

    for phrase in (
        "adult synthetic role-play",
        "no protected health information",
        "non-diagnostic safety-signal routing",
        "simulated human-review queue",
    ):
        assert phrase in agents.casefold()

    assert "Milestone 13 full-stack research contract freeze" in spec
    assert "ReleaseDispositionV1" in spec
    assert "allow / hold_for_review / system_failure" in spec
    assert "status-only SSE plus atomic gated answers" in architecture
    assert "Milestone 13 — full-stack research contract freeze" in plan
    assert "Milestone 17 — final evaluation, cloud template, and delivery" in plan


def test_m13_freezes_api_plugin_persistence_and_identity_boundaries() -> None:
    runtime = _normalized("docs/agent_runtime_contract.md")

    for endpoint in (
        "POST /api/v1/sessions",
        "POST /api/v1/sessions/{session_id}/turns",
        "GET /api/v1/sessions/{session_id}/events",
        "POST /api/v1/reviews/{review_id}/decisions",
        "POST /api/v1/sessions/{session_id}/close",
        "GET /api/v1/sessions/{session_id}/report",
        "GET /api/v1/plugins",
        "PUT /api/v1/plugin-profiles/{profile_id}",
    ):
        assert endpoint in runtime

    for phrase in (
        "last-event-id",
        "participant / reviewer / admin",
        "safety-critical plugins cannot be disabled",
        "postgresql is the authoritative source",
        "redis is never the system of record",
        "30 days",
        "vllm",
        "ollama",
        "deepseek",
    ):
        assert phrase in runtime.casefold()


def test_m13_threat_and_test_matrices_cover_full_stack_failure_modes() -> None:
    threat = _normalized("docs/threat_model.md").casefold()
    matrix = _normalized("docs/test_matrix.md")
    safety = _normalized("docs/safety_and_limitations.md").casefold()

    for phrase in (
        "demo identity enabled in production",
        "sse content leakage",
        "tool-call excessive agency",
        "oidc role bypass",
        "cross-instance event loss",
        "report injection",
    ):
        assert phrase in threat

    assert "Milestone 13 full-stack contract matrix" in matrix
    assert "no model rewrite can establish that a person's risk has cleared" in safety


def test_m13_evidence_registry_is_versioned_linked_and_unapproved() -> None:
    path = ROOT / "evidence" / "evidence_registry.v1.json"
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert set(payload) == {"registry_version", "as_of", "entries"}
    assert payload["registry_version"] == "v1"
    assert payload["as_of"] == "2026-09-02"
    assert len(payload["entries"]) >= 8

    source_ids: list[str] = []
    for entry in payload["entries"]:
        assert set(entry) == {
            "source_id",
            "title",
            "source_type",
            "source_url",
            "intended_use",
            "review_status",
        }
        assert entry["source_url"].startswith("https://")
        assert entry["intended_use"]
        assert entry["review_status"] == "advisor_review_pending"
        source_ids.append(entry["source_id"])

    assert len(source_ids) == len(set(source_ids))
