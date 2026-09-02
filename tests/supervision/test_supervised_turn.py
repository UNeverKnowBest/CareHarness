import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path

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
from careloop.supervision import ReviewQueueStatus
from careloop.supervision.orchestration import SupervisedSyntheticTurn

NOW = datetime(2026, 9, 2, 8, 0, tzinfo=UTC)


class SafeInputRouter:
    def route_input(self, *_args: object, **_kwargs: object) -> None:
        return None


class ThreeDraftModel:
    def __init__(self) -> None:
        self.calls = 0

    async def generate(self, request: ModelRequest) -> ModelDraft:
        index = self.calls
        self.calls += 1
        return ModelDraft(
            contract_version="v1",
            request_id=request.request_id,
            draft_id=f"draft-{index}",
            text=f"[SYNTHETIC] quarantined {index}",
            provider_id="provider-test",
            model_name="model-test",
        )


class ExhaustingGate:
    def check(
        self, draft: ModelDraft, *, input_turn: Turn, rewrite_count: int
    ) -> DraftGateResult:
        del input_turn
        decision = (
            DraftDecision.REWRITE
            if rewrite_count < 2
            else DraftDecision.HOLD_FOR_REVIEW
        )
        disposition = (
            SafetyDisposition.CLARIFICATION_REQUIRED
            if decision is DraftDecision.REWRITE
            else SafetyDisposition.HUMAN_REVIEW_REQUIRED
        )
        return DraftGateResult(
            contract_version="v1",
            draft_id=draft.draft_id,
            decision=decision,
            disposition=disposition,
            rewrite_count=rewrite_count,
            finding_ids=(f"finding-{rewrite_count}",),
        )


def test_durable_supervision_exhausts_two_repairs_then_queues_without_release(
    tmp_path: Path,
) -> None:
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'runtime.db'}")
    metadata.create_all(engine)
    store = PostgresRuntimeStore(engine)
    config = SessionConfig(
        contract_version="v1",
        scenario_id="scenario-m15-en",
        locale="en",
        plugin_profile_id="profile-m15",
    )
    model = ThreeDraftModel()
    runner = RunSyntheticTurn(
        session_id="session-m15",
        session_config=config,
        safety_runtime=SafeInputRouter(),
        model_runtime=ProviderNeutralModelRuntime(
            model_port=model,
            provider_manifest=PluginManifestV1(
                plugin_api_version="v1",
                plugin_id="provider-test",
                plugin_version="1",
                kind=PluginKind.MODEL_PROVIDER,
                capabilities=("synthetic-generation",),
                configuration_schema_id="provider-test.v1",
                dependency_plugin_ids=(),
                failure_mode=PluginFailureMode.CRITICAL_FAIL_CLOSED,
                default_enabled=False,
            ),
            model_name="model-test",
        ),
        draft_gate=ExhaustingGate(),
        ledger=store,
    )
    supervised = SupervisedSyntheticTurn(
        runner=runner,
        review_queue=store,
        locale=config.locale,
    )
    command = SyntheticTurnCommand(
        contract_version="v1",
        request_id="turn-request-m15",
        input_turn=Turn(
            turn_id="turn-user-m15",
            sequence=0,
            role="user",
            text="[SYNTHETIC] Fixed English supervision case.",
        ),
        context_turns=(),
        jurisdiction="ZZ-TEST",
        as_of=NOW.date(),
        prompt_template_id="support-shell.v1",
        prompt_template_hash="sha256:" + "a" * 64,
    )

    result = asyncio.run(
        supervised.execute(
            command,
            enqueued_at=NOW,
            review_target_at=NOW + timedelta(minutes=15),
        )
    )

    assert model.calls == 3
    assert result.turn.participant.released_turn is None
    assert result.review_item is not None
    assert result.review_item.status is ReviewQueueStatus.PENDING
    assert result.review_item.draft == result.turn.quarantined_drafts[-1]
    assert store.review_item(result.review_item.review_id) == result.review_item
