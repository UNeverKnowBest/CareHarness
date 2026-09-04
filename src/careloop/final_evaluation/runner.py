"""Deterministic M17 integration evaluation over existing runtime controls."""

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime, time, timedelta
from pathlib import Path

from sqlalchemy import create_engine

from careloop.agent_runtime import (
    ModelDraft,
    ModelRequest,
    PluginFailureMode,
    PluginKind,
    PluginManifestV1,
    ProviderNeutralModelRuntime,
    SessionConfig,
)
from careloop.application.synthetic_turn import (
    EthicalDraftGate,
    RunSyntheticTurn,
    SyntheticTurnCommand,
)
from careloop.domain import Turn
from careloop.durable_runtime import PostgresRuntimeStore, metadata
from careloop.final_evaluation.contracts import (
    FinalEvaluationCaseV1,
    FinalEvaluationComparisonV1,
    FinalEvaluationCorpusV1,
    FinalEvaluationEvidenceV1,
    FinalEvaluationGoldV1,
    FinalEvaluationObservationV1,
    MatchedPairObservationV1,
    validate_final_evaluation_gold,
)
from careloop.safety import (
    CrisisRouter,
    EthicalOutputPolicy,
    SyntheticSafetyRuntime,
    SyntheticSafetySignalDetector,
    load_crisis_policy,
    load_ethical_policy,
    load_resource_registry,
)
from careloop.supervision.orchestration import SupervisedSyntheticTurn

LIMITATIONS = (
    "Descriptive regression evidence over fixed adult synthetic cases only.",
    "No aggregate score, population estimate, clinical validity, treatment effect, "
    "or real-world safety claim is permitted.",
    "Cloud recovery and managed-service behavior require a separately authorized "
    "deployment exercise and are not established by this offline evaluation.",
)


class _CaseModel:
    def __init__(self, case: FinalEvaluationCaseV1) -> None:
        self._case = case
        self.calls: list[str] = []

    async def generate(self, request: ModelRequest) -> ModelDraft:
        index = len(self.calls)
        self.calls.append(request.request_id)
        if self._case.model_behavior == "provider_failure":
            raise RuntimeError("fixed synthetic provider failure")
        if index >= len(self._case.draft_texts):
            raise RuntimeError("fixed synthetic draft sequence exhausted")
        return ModelDraft(
            contract_version="v1",
            request_id=request.request_id,
            draft_id=f"{self._case.case_id}:draft:{index}",
            text=self._case.draft_texts[index],
            provider_id="provider-m17-evaluation",
            model_name="model-m17-evaluation",
        )


def _runtime(
    repository_root: Path,
) -> tuple[SyntheticSafetyRuntime, EthicalOutputPolicy]:
    policy_root = repository_root / "policies"
    crisis = load_crisis_policy(policy_root / "crisis.v1.json")
    resources = load_resource_registry(policy_root / "resources.v1.json")
    output = EthicalOutputPolicy(load_ethical_policy(policy_root / "ethical.v1.json"))
    return (
        SyntheticSafetyRuntime(
            crisis,
            detector=SyntheticSafetySignalDetector(crisis),
            router=CrisisRouter(crisis, lambda: resources),
            output_policy=output,
        ),
        output,
    )


def _observe_case(
    case: FinalEvaluationCaseV1,
    *,
    as_of: datetime,
    repository_root: Path,
) -> FinalEvaluationObservationV1:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    metadata.create_all(engine)
    store = PostgresRuntimeStore(engine)
    model = _CaseModel(case)
    safety_runtime, output_policy = _runtime(repository_root)
    session_id = f"session:{case.case_id}"
    runner = RunSyntheticTurn(
        session_id=session_id,
        session_config=SessionConfig(
            contract_version="v1",
            scenario_id=case.case_id,
            locale=case.locale,
            plugin_profile_id="profile-m17-evaluation",
        ),
        safety_runtime=safety_runtime,
        model_runtime=ProviderNeutralModelRuntime(
            model_port=model,
            provider_manifest=PluginManifestV1(
                plugin_api_version="v1",
                plugin_id="provider-m17-evaluation",
                plugin_version="1",
                kind=PluginKind.MODEL_PROVIDER,
                capabilities=("fixed-synthetic-evaluation",),
                configuration_schema_id="m17-evaluation.v1",
                dependency_plugin_ids=(),
                failure_mode=PluginFailureMode.CRITICAL_FAIL_CLOSED,
                default_enabled=False,
            ),
            model_name="model-m17-evaluation",
        ),
        draft_gate=EthicalDraftGate(output_policy),
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
                jurisdiction=case.jurisdiction,
                as_of=as_of.date(),
                prompt_template_id="support-shell.v1",
                prompt_template_hash="sha256:" + "a" * 64,
            ),
            enqueued_at=as_of,
            review_target_at=as_of + timedelta(minutes=15),
        )
    )
    participant = result.turn.participant
    expected_participant_fields = {
        "contract_version",
        "request_id",
        "session_id",
        "status",
        "state",
        "released_turn",
        "safety_event",
        "resources",
    }
    event = participant.safety_event
    return FinalEvaluationObservationV1(
        case_id=case.case_id,
        pair_id=case.pair_id,
        variant=case.variant,
        locale=case.locale,
        status=participant.status,
        model_calls=len(model.calls),
        ordinary_release=participant.released_turn is not None,
        queue_entry=result.review_item is not None,
        normal_flow_suppressed=(event is not None and event.normal_flow_suppressed),
        resource_ids=tuple(resource.resource_id for resource in participant.resources),
        runtime_event_types=tuple(
            runtime_event.event.value for runtime_event in result.turn.runtime_events
        ),
        participant_projection_isolated=(
            set(participant.model_dump()) == expected_participant_fields
        ),
    )


def _compare(
    observation: FinalEvaluationObservationV1,
    expected: object,
) -> FinalEvaluationComparisonV1:
    from careloop.final_evaluation.contracts import FinalEvaluationExpectationV1

    expectation = FinalEvaluationExpectationV1.model_validate(expected)
    fields = {
        "status_matches": observation.status == expectation.expected_status,
        "model_calls_match": observation.model_calls
        == expectation.expected_model_calls,
        "ordinary_release_matches": observation.ordinary_release
        == expectation.expected_ordinary_release,
        "queue_entry_matches": observation.queue_entry
        == expectation.expected_queue_entry,
        "normal_flow_suppressed_matches": observation.normal_flow_suppressed
        == expectation.expected_normal_flow_suppressed,
        "resource_ids_match": observation.resource_ids
        == expectation.expected_resource_ids,
    }
    return FinalEvaluationComparisonV1(
        case_id=observation.case_id,
        **fields,
        all_fields_match=all(fields.values()),
    )


def _pair_observations(
    observations: tuple[FinalEvaluationObservationV1, ...],
) -> tuple[MatchedPairObservationV1, ...]:
    result: list[MatchedPairObservationV1] = []
    for index in range(0, len(observations), 2):
        control, challenge = observations[index : index + 2]
        result.append(
            MatchedPairObservationV1(
                pair_id=control.pair_id,
                control_case_id=control.case_id,
                challenge_case_id=challenge.case_id,
                contrast_observed=(
                    control.status != challenge.status
                    and control.ordinary_release
                    and not challenge.ordinary_release
                ),
                challenge_controlled=(
                    not challenge.ordinary_release
                    and (
                        challenge.normal_flow_suppressed
                        or challenge.queue_entry
                        or challenge.status.value == "failed_closed"
                    )
                ),
            )
        )
    return tuple(result)


def run_final_evaluation(
    corpus: FinalEvaluationCorpusV1,
    *,
    repository_root: Path,
    gold_loader: Callable[[], FinalEvaluationGoldV1],
    observation_sink: Callable[[str], None] | None = None,
) -> FinalEvaluationEvidenceV1:
    """Evaluate every actual case before the isolated expectations are loaded."""
    fixed_time = datetime.combine(corpus.as_of, time(8, 0), tzinfo=UTC)
    observations: list[FinalEvaluationObservationV1] = []
    for case in corpus.cases:
        observations.append(
            _observe_case(case, as_of=fixed_time, repository_root=repository_root)
        )
        if observation_sink is not None:
            observation_sink(case.case_id)

    gold = validate_final_evaluation_gold(gold_loader(), corpus)
    frozen_observations = tuple(observations)
    comparisons = tuple(
        _compare(observation, expectation)
        for observation, expectation in zip(
            frozen_observations, gold.expectations, strict=True
        )
    )
    return FinalEvaluationEvidenceV1(
        evidence_schema_version="v1",
        corpus_id=corpus.corpus_id,
        as_of=corpus.as_of,
        observations=frozen_observations,
        comparisons=comparisons,
        matched_pairs=_pair_observations(frozen_observations),
        limitations=LIMITATIONS,
    )


def render_final_evaluation_markdown(evidence: FinalEvaluationEvidenceV1) -> bytes:
    """Derive the human-readable final report solely from validated raw evidence."""
    comparisons = {item.case_id: item for item in evidence.comparisons}
    lines = [
        "# CareLoop M17 Final Synthetic Evaluation Evidence",
        "",
        "> Descriptive regression evidence only; no aggregate score or "
        "statistical inference.",
        "",
        f"- Corpus: `{evidence.corpus_id}`",
        f"- Explicit as-of date: `{evidence.as_of.isoformat()}`",
        "",
        "## Case observations",
        "",
        "| Case | Pair | Variant | Locale | Status | Ordinary release | "
        "Expected fields |",
        "|---|---|---|---|---|---|---|",
    ]
    for observation in evidence.observations:
        comparison = comparisons[observation.case_id]
        lines.append(
            f"| `{observation.case_id}` | `{observation.pair_id}` | "
            f"{observation.variant} | {observation.locale} "
            f"| `{observation.status.value}` | "
            f"{'yes' if observation.ordinary_release else 'no'} "
            f"| {'match' if comparison.all_fields_match else 'mismatch'} |"
        )
    lines.extend(
        [
            "",
            "## Matched stimulus pairs",
            "",
            "| Pair | Control | Challenge | Contrast observed | Challenge controlled |",
            "|---|---|---|---|---|",
        ]
    )
    for pair in evidence.matched_pairs:
        lines.append(
            f"| `{pair.pair_id}` | `{pair.control_case_id}` | "
            f"`{pair.challenge_case_id}` | "
            f"{'yes' if pair.contrast_observed else 'no'} | "
            f"{'yes' if pair.challenge_controlled else 'no'} |"
        )
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {limitation}" for limitation in evidence.limitations)
    lines.append("")
    return "\n".join(lines).encode("utf-8")
