import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine

from careloop.agent_runtime import (
    DraftDecision,
    DraftGateResult,
    ModelDraft,
    ModelRequest,
    PluginFailureMode,
    PluginKind,
    PluginManifestV1,
    ProviderNeutralModelRuntime,
    SafetyDisposition,
    SessionConfig,
)
from careloop.application.synthetic_turn import RunSyntheticTurn, SyntheticTurnCommand
from careloop.domain import Turn
from careloop.durable_runtime import PostgresRuntimeStore, metadata
from careloop.safety import (
    CrisisRouter,
    EthicalOutputPolicy,
    SyntheticSafetyRuntime,
    SyntheticSafetySignalDetector,
    load_crisis_policy,
    load_ethical_policy,
    load_resource_registry,
)
from careloop.supervision.corpus import SupervisionCaseV1, load_supervision_corpus
from careloop.supervision.orchestration import SupervisedSyntheticTurn

ROOT = Path(__file__).parents[2]
CORPUS = load_supervision_corpus(
    ROOT / "benchmarks" / "supervision" / "m15.supervision.v1.json"
)
NOW = datetime(2026, 8, 29, 8, 0, tzinfo=UTC)


class CorpusModel:
    def __init__(self, case: SupervisionCaseV1) -> None:
        self._case = case
        self.calls: list[str] = []

    async def generate(self, request: ModelRequest) -> ModelDraft:
        index = len(self.calls)
        self.calls.append(request.request_id)
        return ModelDraft(
            contract_version="v1",
            request_id=request.request_id,
            draft_id=f"{self._case.case_id}:draft:{index}",
            text=self._case.draft_texts[index],
            provider_id="provider-corpus-test",
            model_name="model-corpus-test",
        )


class CorpusGate:
    def __init__(self, case: SupervisionCaseV1) -> None:
        self._case = case
        self.calls = 0

    def check(
        self, draft: ModelDraft, *, input_turn: Turn, rewrite_count: int
    ) -> DraftGateResult:
        del input_turn
        decision = self._case.gate_decisions[self.calls]
        self.calls += 1
        disposition = {
            DraftDecision.ALLOW: SafetyDisposition.SUPPORT_ALLOWED,
            DraftDecision.REWRITE: SafetyDisposition.CLARIFICATION_REQUIRED,
            DraftDecision.HOLD_FOR_REVIEW: SafetyDisposition.HUMAN_REVIEW_REQUIRED,
            DraftDecision.SUPPRESS_FOR_GUIDANCE: (
                SafetyDisposition.EMERGENCY_GUIDANCE_REQUIRED
            ),
        }[decision]
        findings = (
            () if decision is DraftDecision.ALLOW else (f"finding-{rewrite_count}",)
        )
        return DraftGateResult(
            contract_version="v1",
            draft_id=draft.draft_id,
            decision=decision,
            disposition=disposition,
            rewrite_count=rewrite_count,
            finding_ids=findings,
        )


def _safety_runtime() -> SyntheticSafetyRuntime:
    policy_root = ROOT / "policies"
    crisis = load_crisis_policy(policy_root / "crisis.v1.json")
    ethical = load_ethical_policy(policy_root / "ethical.v1.json")
    resources = load_resource_registry(policy_root / "resources.v1.json")
    return SyntheticSafetyRuntime(
        crisis,
        detector=SyntheticSafetySignalDetector(crisis),
        router=CrisisRouter(crisis, lambda: resources),
        output_policy=EthicalOutputPolicy(ethical),
    )


def test_fixed_bilingual_golden_red_team_corpus_is_strict_and_complete() -> None:
    path = ROOT / "benchmarks" / "supervision" / "m15.supervision.v1.json"
    corpus = load_supervision_corpus(path)

    assert corpus.contract_version == "v1"
    assert len(corpus.cases) == 8
    assert {case.locale for case in corpus.cases} == {"en", "zh-CN"}
    assert {case.case_kind for case in corpus.cases} == {
        "safe_allow",
        "input_override",
        "repair_allow",
        "repair_exhausted",
    }
    for locale in ("en", "zh-CN"):
        localized = tuple(case for case in corpus.cases if case.locale == locale)
        assert {case.case_kind for case in localized} == {
            "safe_allow",
            "input_override",
            "repair_allow",
            "repair_exhausted",
        }
    assert all(case.synthetic_only for case in corpus.cases)
    assert all(
        not case.expected_ordinary_release
        for case in corpus.cases
        if case.case_kind in {"input_override", "repair_exhausted"}
    )


@pytest.mark.parametrize("case", CORPUS.cases, ids=lambda case: case.case_id)
def test_fixed_case_drives_supervised_runtime_observations(
    case: SupervisionCaseV1,
) -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    metadata.create_all(engine)
    store = PostgresRuntimeStore(engine)
    model = CorpusModel(case)
    gate = CorpusGate(case)
    runner = RunSyntheticTurn(
        session_id=f"session:{case.case_id}",
        session_config=SessionConfig(
            contract_version="v1",
            scenario_id=case.case_id,
            locale=case.locale,
            plugin_profile_id="profile-m15-corpus",
        ),
        safety_runtime=_safety_runtime(),
        model_runtime=ProviderNeutralModelRuntime(
            model_port=model,
            provider_manifest=PluginManifestV1(
                plugin_api_version="v1",
                plugin_id="provider-corpus-test",
                plugin_version="1",
                kind=PluginKind.MODEL_PROVIDER,
                capabilities=("synthetic-generation",),
                configuration_schema_id="provider-corpus.v1",
                dependency_plugin_ids=(),
                failure_mode=PluginFailureMode.CRITICAL_FAIL_CLOSED,
                default_enabled=False,
            ),
            model_name="model-corpus-test",
        ),
        draft_gate=gate,
        ledger=store,
    )
    supervised = SupervisedSyntheticTurn(
        runner=runner,
        review_queue=store,
        locale=case.locale,
    )
    result = asyncio.run(
        supervised.execute(
            SyntheticTurnCommand(
                contract_version="v1",
                request_id=f"request:{case.case_id}",
                input_turn=Turn(
                    turn_id=f"turn:{case.case_id}:user",
                    sequence=0,
                    role="user",
                    text=case.input_text,
                ),
                context_turns=(),
                jurisdiction="ZZ-TEST",
                as_of=NOW.date(),
                prompt_template_id="support-shell.v1",
                prompt_template_hash="sha256:" + "a" * 64,
            ),
            enqueued_at=NOW,
            review_target_at=NOW + timedelta(minutes=15),
        )
    )

    assert result.turn.participant.status is case.expected_status
    assert len(model.calls) == case.expected_model_calls
    assert (result.turn.participant.released_turn is not None) is (
        case.expected_ordinary_release
    )
    assert (result.review_item is not None) is case.expected_queue_entry
