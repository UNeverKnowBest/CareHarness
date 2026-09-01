from pathlib import Path


def test_m9_contract_freezes_plugin_and_model_runtime_boundaries() -> None:
    specification = Path("SPEC.md").read_text(encoding="utf-8")
    architecture = Path("ARCHITECTURE.md").read_text(encoding="utf-8")
    runtime_contract = " ".join(
        Path("docs/agent_runtime_contract.md").read_text(encoding="utf-8").split()
    )
    test_matrix = Path("docs/test_matrix.md").read_text(encoding="utf-8")

    required = (
        "careloop.plugins.v1",
        "PluginAllowlistV1",
        "dependency-before-dependant",
        "ProviderNeutralModelRuntime",
        "quarantined_draft",
        "ModelRuntimeFailureCode",
        "RUNTIME_FAILURE",
        "FAILED_CLOSED",
        "deterministic test adapter",
    )
    combined = "\n".join((specification, architecture, runtime_contract, test_matrix))
    for text in required:
        assert text in combined


def test_m9_documents_keep_real_plugins_cloud_and_session_orchestration_deferred() -> (
    None
):
    runtime_contract = " ".join(
        Path("docs/agent_runtime_contract.md").read_text(encoding="utf-8").split()
    )

    for text in (
        "No plugin package is bundled or enabled by default",
        "no real provider adapter",
        "no network call",
        "session orchestration remains deferred",
    ):
        assert text in runtime_contract
