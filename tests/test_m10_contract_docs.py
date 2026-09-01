from pathlib import Path


def test_m10_contract_freezes_orchestration_ledger_and_projection_boundaries() -> None:
    combined = " ".join(
        "\n".join(
            Path(path).read_text(encoding="utf-8")
            for path in (
                "SPEC.md",
                "ARCHITECTURE.md",
                "docs/agent_runtime_contract.md",
                "docs/test_matrix.md",
                "docs/threat_model.md",
            )
        ).split()
    )

    for text in (
        "RunSyntheticTurn",
        "SyntheticTurnCommand",
        "ParticipantTurnView",
        "ResearchReviewTurnView",
        "input pre-route",
        "DRAFT_APPROVED",
        "maximum two",
        "InMemoryRuntimeEventLedger",
        "append-only",
        "no update/delete",
    ):
        assert text in combined


def test_m10_contract_keeps_external_and_clinical_capabilities_excluded() -> None:
    specification = Path("SPEC.md").read_text(encoding="utf-8")

    for text in (
        "No real plugin/provider",
        "network",
        "database",
        "new CLI command",
        "real-person data",
        "clinical screening",
        "risk classification",
    ):
        assert text in specification
