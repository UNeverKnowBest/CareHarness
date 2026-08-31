from pathlib import Path


def test_m8_runtime_contract_freezes_public_surface() -> None:
    contract = Path("docs/agent_runtime_contract.md").read_text(encoding="utf-8")

    required = (
        "synthetic role-play",
        "POST /v1/demo-sessions",
        "POST /v1/demo-sessions/{id}/turns",
        "GET /v1/demo-sessions/{id}/events",
        "POST /v1/review-tasks/{id}/decisions",
        "GET /v1/demo-sessions/{id}/reports/{audience}",
        "PluginManifestV1",
        "runtime_events",
        "append-only",
        "No raw model token",
        "two rewrite attempts",
    )
    for text in required:
        assert text in contract


def test_m8_threat_model_covers_release_privacy_and_plugin_boundaries() -> None:
    threat_model = Path("docs/threat_model.md").read_text(encoding="utf-8")

    required = (
        "Prompt injection",
        "Unsafe draft release",
        "Provider failure",
        "Plugin supply chain",
        "Audit tampering",
        "Role boundary",
        "Synthetic data only",
        "fail closed",
        "chain-of-thought",
    )
    for text in required:
        assert text in threat_model
