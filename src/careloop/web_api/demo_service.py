"""Local adult-synthetic service composition used by M16 tests and Compose."""

import asyncio
import json
from collections.abc import Callable, Iterable
from datetime import datetime, timedelta
from pathlib import Path

from pydantic import BaseModel, JsonValue
from sqlalchemy import Engine, text

from careloop.agent_runtime import (
    ModelDraft,
    ModelRequest,
    PluginFailureMode,
    PluginKind,
    PluginManifestV1,
    ProviderNeutralModelRuntime,
    ReviewDecision,
    SessionConfig,
)
from careloop.application.evaluate_trajectory import EvaluateTrajectory
from careloop.application.synthetic_close import (
    CloseSyntheticSession,
    SyntheticSessionCloseCommand,
    SyntheticSessionSnapshot,
)
from careloop.application.synthetic_review import SyntheticReviewCommand
from careloop.application.synthetic_turn import (
    EthicalDraftGate,
    RunSyntheticTurn,
    SyntheticTurnCommand,
    SyntheticTurnStatus,
)
from careloop.artifacts import canonical_sha256
from careloop.domain import Turn
from careloop.durable_runtime import (
    PluginProfileEntryV1,
    PluginProfileV1,
    PostgresRuntimeStore,
    metadata,
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
from careloop.supervision.review_resolution import (
    QueuedSyntheticReviewCommand,
    ResolveQueuedSyntheticReview,
)
from careloop.web_api.contracts import (
    CloseSessionRequestV1,
    CreateSessionRequestV1,
    ParticipantSessionV1,
    PluginProfileUpdateRequestV1,
    PublicSessionStateV1,
    ReleaseDispositionV1,
    ReviewDecisionRequestV1,
    SseEventTypeV1,
    SseEventV1,
    SubmitTurnRequestV1,
)
from careloop.web_api.identity import IdentityContextV1, IdentityRole, require_role
from careloop.web_api.reports import ParticipantSummaryV1, ResearchReportV1
from careloop.web_api.repository import ResearchWebRepository, StoredResearchSessionV1


class _DeterministicDemoModel:
    """Local fixed model port; it performs no network or user-directed action."""

    provider_id = "provider-local-deterministic"
    model_name = "deterministic-demo-v1"

    async def generate(self, request: ModelRequest) -> ModelDraft:
        text_value = (
            "[SYNTHETIC] 我们可以一步一步进行这次虚构演练，你可以选择从哪里开始。"
            if request.locale == "zh-CN"
            else "[SYNTHETIC] We can take this fictional rehearsal one step at a "
            "time, and you can choose where to begin."
        )
        return ModelDraft(
            contract_version="v1",
            request_id=request.request_id,
            draft_id=f"{request.request_id}:complete-draft",
            text=text_value,
            provider_id=self.provider_id,
            model_name=self.model_name,
        )


class LocalResearchService:
    """Compose existing safety/evaluation services for fixed local seed scenarios."""

    def __init__(
        self,
        *,
        engine: Engine,
        repository_root: Path,
        clock: Callable[[], datetime],
    ) -> None:
        self._root = repository_root
        self._clock = clock
        metadata.create_all(engine)
        self._runtime = PostgresRuntimeStore(engine)
        self._web = ResearchWebRepository(engine)
        self._engine = engine
        seeds = json.loads(
            (repository_root / "seeds" / "scenarios.v1.json").read_text("utf-8")
        )
        self._scenarios = {item["scenario_id"]: item for item in seeds["scenarios"]}
        policy_root = repository_root / "policies"
        crisis = load_crisis_policy(policy_root / "crisis.v1.json")
        resources = load_resource_registry(policy_root / "resources.v1.json")
        ethical = load_ethical_policy(policy_root / "ethical.v1.json")
        self._output_policy = EthicalOutputPolicy(ethical)
        self._safety = SyntheticSafetyRuntime(
            crisis,
            detector=SyntheticSafetySignalDetector(crisis),
            router=CrisisRouter(crisis, lambda: resources),
            output_policy=self._output_policy,
        )
        self._evaluator = EvaluateTrajectory.from_paths(
            benchmark_manifest_path=repository_root / "benchmarks" / "manifest.v1.json",
            process_policy_path=policy_root / "process.v1.json",
            crisis_policy_path=policy_root / "crisis.v1.json",
            resource_policy_path=policy_root / "resources.v1.json",
            evaluation_policy_path=policy_root / "evaluation.v1.json",
        )
        self._ensure_local_profile()

    def create_session(
        self,
        request: CreateSessionRequestV1,
        *,
        idempotency_key: str,
        identity: IdentityContextV1,
    ) -> ParticipantSessionV1:
        require_role(identity, IdentityRole.PARTICIPANT)
        self._validate_idempotency_key(idempotency_key)
        scenario = self._scenarios.get(request.scenario_id)
        if scenario is None or scenario["locale"] != request.locale:
            raise ValueError("scenario and locale must match a fixed local seed")
        if request.model_id != _DeterministicDemoModel.model_name:
            raise ValueError("local service accepts only the deterministic demo model")
        request_hash = self._request_hash(idempotency_key, request, identity)
        idempotency_request_id = f"api:create:{idempotency_key}"
        cached = self._runtime.idempotency_result(
            request.session_id, idempotency_request_id
        )
        if cached is not None:
            self._runtime.record_idempotency(
                session_id=request.session_id,
                request_id=idempotency_request_id,
                request_hash=request_hash,
                result_payload=cached,
            )
            return ParticipantSessionV1.model_validate(cached)
        try:
            stored = self._web.load_session(request.session_id)
        except KeyError:
            stored = None
        if stored is not None:
            self._require_owner(stored.owner_subject, identity)
            raise ValueError("research session identity already exists")

        config = self._session_config(request)
        self._runner(request.session_id, config)
        participant = ParticipantSessionV1(
            contract_version="v1",
            session_id=request.session_id,
            locale=request.locale,
            public_state=PublicSessionStateV1.READY,
            release_disposition=ReleaseDispositionV1.ALLOW,
            released_turns=(),
        )
        now = self._aware_now()
        event = self._public_event(
            participant,
            sequence=0,
            event_type=SseEventTypeV1.STATE_CHANGED,
        )
        self._web.create_session(
            request=request,
            participant=participant,
            owner_subject=identity.subject,
            created_at=now,
            retention_until=(now + timedelta(days=30)).date(),
            event=event,
        )
        self._runtime.record_idempotency(
            session_id=request.session_id,
            request_id=idempotency_request_id,
            request_hash=request_hash,
            result_payload=participant.model_dump(mode="json"),
        )
        return participant

    def submit_turn(
        self,
        session_id: str,
        request: SubmitTurnRequestV1,
        *,
        idempotency_key: str,
        identity: IdentityContextV1,
    ) -> ParticipantSessionV1:
        require_role(identity, IdentityRole.PARTICIPANT)
        self._validate_idempotency_key(idempotency_key)
        stored = self._owned_session(session_id, identity)
        request_hash = self._request_hash(idempotency_key, request, identity)
        cached = self._runtime.idempotency_result(session_id, request.request_id)
        if cached is not None:
            self._runtime.record_idempotency(
                session_id=session_id,
                request_id=request.request_id,
                request_hash=request_hash,
                result_payload=cached,
            )
            return ParticipantSessionV1.model_validate(cached)
        expected_sequence = 0 if not stored.turns else stored.turns[-1].sequence + 1
        if request.sequence != expected_sequence:
            raise ValueError("participant turn sequence must follow stored transcript")
        input_turn = Turn(
            turn_id=request.turn_id,
            sequence=request.sequence,
            role="user",
            text=request.text,
        )
        runner = self._runner(session_id, self._session_config(stored.request))
        supervised = SupervisedSyntheticTurn(
            runner=runner,
            review_queue=self._runtime,
            locale=stored.request.locale,
        )
        now = self._aware_now()
        result = asyncio.run(
            supervised.execute(
                SyntheticTurnCommand(
                    contract_version="v1",
                    request_id=request.request_id,
                    input_turn=input_turn,
                    context_turns=stored.turns,
                    jurisdiction="ZZ-TEST",
                    as_of=now.date(),
                    prompt_template_id="support-shell.v1",
                    prompt_template_hash="sha256:" + "a" * 64,
                ),
                enqueued_at=now,
                review_target_at=now + timedelta(minutes=15),
            )
        )
        participant_result = result.turn.participant
        turns = stored.turns + (input_turn,)
        safety_events = stored.safety_events
        if participant_result.safety_event is not None:
            safety_events += (participant_result.safety_event,)
        released = participant_result.released_turn
        if released is not None:
            turns += (released,)
        public_state, disposition, event_type = self._turn_public_outcome(
            participant_result.status
        )
        participant = ParticipantSessionV1(
            contract_version="v1",
            session_id=session_id,
            locale=stored.request.locale,
            public_state=public_state,
            release_disposition=disposition,
            released_turns=stored.participant.released_turns
            + (() if released is None else (released,)),
        )
        event = self._public_event(
            participant,
            sequence=self._web.next_event_sequence(session_id),
            event_type=event_type,
            released_turn=released,
        )
        self._web.update_session(
            participant=participant,
            turns=turns,
            safety_events=safety_events,
            event=event,
        )
        self._runtime.record_idempotency(
            session_id=session_id,
            request_id=request.request_id,
            request_hash=request_hash,
            result_payload=participant.model_dump(mode="json"),
        )
        return participant

    def get_session(
        self, session_id: str, *, identity: IdentityContextV1
    ) -> ParticipantSessionV1:
        require_role(identity, IdentityRole.PARTICIPANT)
        return self._owned_session(session_id, identity).participant

    def stream_events(
        self,
        session_id: str,
        *,
        after_event_id: str | None,
        identity: IdentityContextV1,
    ) -> Iterable[SseEventV1]:
        require_role(identity, IdentityRole.PARTICIPANT)
        self._owned_session(session_id, identity)
        return self._web.events_after(session_id, after_event_id)

    def close_session(
        self,
        session_id: str,
        request: CloseSessionRequestV1,
        *,
        idempotency_key: str,
        identity: IdentityContextV1,
    ) -> ParticipantSessionV1:
        require_role(identity, IdentityRole.PARTICIPANT)
        self._validate_idempotency_key(idempotency_key)
        stored = self._owned_session(session_id, identity)
        request_hash = self._request_hash(idempotency_key, request, identity)
        cached = self._runtime.idempotency_result(session_id, request.request_id)
        if cached is not None:
            self._runtime.record_idempotency(
                session_id=session_id,
                request_id=request.request_id,
                request_hash=request_hash,
                result_payload=cached,
            )
            return ParticipantSessionV1.model_validate(cached)
        close = CloseSyntheticSession(
            ledger=self._runtime,
            snapshot=SyntheticSessionSnapshot(
                contract_version="v1",
                session_id=session_id,
                trajectory_id=request.trajectory_id,
                turns=stored.turns,
                process_markers=(),
                safety_events=stored.safety_events,
            ),
            evaluator=self._evaluator,
        )
        result = close.execute(
            SyntheticSessionCloseCommand(
                contract_version="v1",
                request_id=request.request_id,
                session_id=session_id,
                trajectory_id=request.trajectory_id,
                evidence_ids=request.evidence_ids,
            )
        )
        if result.evaluation is None:
            public_state = PublicSessionStateV1.FAILED_CLOSED
            disposition = ReleaseDispositionV1.SYSTEM_FAILURE
            event_type = SseEventTypeV1.FAILED_CLOSED
        else:
            public_state = PublicSessionStateV1.CLOSED
            disposition = ReleaseDispositionV1.ALLOW
            event_type = SseEventTypeV1.SESSION_CLOSED
        participant = stored.participant.model_copy(
            update={
                "public_state": public_state,
                "release_disposition": disposition,
            }
        )
        participant = ParticipantSessionV1.model_validate(participant.model_dump())
        report = ResearchReportV1(
            contract_version="v1",
            report_id=f"{session_id}:report:v1",
            session_id=session_id,
            created_at=self._aware_now(),
            participant_summary=self._summary(participant),
            evidence={
                "evaluation": (
                    None
                    if result.evaluation is None
                    else result.evaluation.model_dump(mode="json")
                ),
                "review_queue_is_simulated": True,
                "runtime_event_id": result.runtime_event.event_id,
            },
        )
        event = self._public_event(
            participant,
            sequence=self._web.next_event_sequence(session_id),
            event_type=event_type,
        )
        self._web.update_session(
            participant=participant,
            turns=stored.turns,
            safety_events=stored.safety_events,
            event=event,
            report=report,
        )
        self._runtime.record_idempotency(
            session_id=session_id,
            request_id=request.request_id,
            request_hash=request_hash,
            result_payload=participant.model_dump(mode="json"),
        )
        return participant

    def get_report(
        self, session_id: str, *, identity: IdentityContextV1
    ) -> ResearchReportV1:
        require_role(
            identity,
            IdentityRole.PARTICIPANT,
            IdentityRole.REVIEWER,
            IdentityRole.ADMIN,
        )
        stored = self._web.load_session(session_id)
        if identity.role is IdentityRole.PARTICIPANT:
            self._require_owner(stored.owner_subject, identity)
        if stored.report is None:
            raise ValueError("report is unavailable until the session is closed")
        return stored.report

    def decide_review(
        self,
        review_id: str,
        request: ReviewDecisionRequestV1,
        *,
        idempotency_key: str,
        identity: IdentityContextV1,
    ) -> ParticipantSessionV1:
        require_role(identity, IdentityRole.REVIEWER)
        self._validate_idempotency_key(idempotency_key)
        item = self._runtime.review_item(review_id)
        reviewer_id = f"synthetic-reviewer:{identity.subject}"
        expected = request.expected_revision
        if expected == 0:
            item = self._runtime.claim_review(
                review_id,
                reviewer_id=reviewer_id,
                expected_revision=0,
                claimed_at=request.resolved_at,
            )
            expected = item.revision
        stored = self._web.load_session(item.session_id)
        last_user = next(turn for turn in reversed(stored.turns) if turn.role == "user")
        release_turn: Turn | None = None
        if request.decision is ReviewDecision.APPROVE:
            release_turn = Turn(
                turn_id=f"{last_user.turn_id}:assistant",
                sequence=last_user.sequence + 1,
                role="assistant",
                text=item.draft.text,
            )
        elif request.decision is ReviewDecision.REPLACE_WITH_SAFE_TEMPLATE:
            release_turn = request.replacement_turn
        resolved = ResolveQueuedSyntheticReview(store=self._runtime).execute(
            QueuedSyntheticReviewCommand(
                contract_version="v1",
                review_id=review_id,
                reviewer_id=reviewer_id,
                expected_revision=expected,
                resolved_at=request.resolved_at,
                review=SyntheticReviewCommand(
                    contract_version="v1",
                    request_id=request.request_id,
                    session_id=item.session_id,
                    decision=request.decision,
                    reviewed_draft=item.draft,
                    release_turn=release_turn,
                    evidence_ids=request.evidence_ids,
                ),
            )
        )
        released = resolved.resolution.participant.released_turn
        turns = stored.turns + (() if released is None else (released,))
        participant = ParticipantSessionV1(
            contract_version="v1",
            session_id=item.session_id,
            locale=stored.request.locale,
            public_state=(
                PublicSessionStateV1.ANSWER_AVAILABLE
                if released is not None
                else PublicSessionStateV1.CLOSED
            ),
            release_disposition=(
                ReleaseDispositionV1.ALLOW
                if released is not None
                else ReleaseDispositionV1.HOLD_FOR_REVIEW
            ),
            released_turns=stored.participant.released_turns
            + (() if released is None else (released,)),
        )
        event = self._public_event(
            participant,
            sequence=self._web.next_event_sequence(item.session_id),
            event_type=(
                SseEventTypeV1.ANSWER_RELEASED
                if released is not None
                else SseEventTypeV1.SESSION_CLOSED
            ),
            released_turn=released,
        )
        self._web.update_session(
            participant=participant,
            turns=turns,
            safety_events=stored.safety_events,
            event=event,
        )
        return participant

    def list_plugins(self, *, identity: IdentityContextV1) -> dict[str, JsonValue]:
        require_role(identity, IdentityRole.ADMIN)
        profile = self._runtime.load_plugin_profile("profile-local-v1")
        plugins: list[JsonValue] = []
        for item in profile.plugins:
            payload = item.model_dump(mode="json")
            payload["locked_reason"] = (
                "safety_critical" if item.locked else "optional_next_session_only"
            )
            plugins.append(payload)
        return {"contract_version": "v1", "plugins": plugins}

    def replace_plugin_profile(
        self,
        profile_id: str,
        request: PluginProfileUpdateRequestV1,
        *,
        idempotency_key: str,
        identity: IdentityContextV1,
    ) -> dict[str, JsonValue]:
        require_role(identity, IdentityRole.ADMIN)
        self._validate_idempotency_key(idempotency_key)
        profile = PluginProfileV1(
            contract_version="v1",
            profile_id=profile_id,
            profile_version=request.profile_version,
            plugins=tuple(
                PluginProfileEntryV1.model_validate(item) for item in request.plugins
            ),
        )
        self._runtime.save_plugin_profile(profile)
        return {
            "contract_version": "v1",
            "profile_id": profile.profile_id,
            "profile_version": profile.profile_version,
        }

    def ready(self) -> bool:
        try:
            with self._engine.connect() as connection:
                connection.execute(text("SELECT 1"))
        except Exception:
            return False
        return True

    def _runner(self, session_id: str, config: SessionConfig) -> RunSyntheticTurn:
        model = _DeterministicDemoModel()
        manifest = PluginManifestV1(
            plugin_api_version="v1",
            plugin_id=model.provider_id,
            plugin_version="1",
            kind=PluginKind.MODEL_PROVIDER,
            capabilities=("fixed-synthetic-generation",),
            configuration_schema_id="local-deterministic.v1",
            dependency_plugin_ids=(),
            failure_mode=PluginFailureMode.CRITICAL_FAIL_CLOSED,
            default_enabled=False,
        )
        return RunSyntheticTurn(
            session_id=session_id,
            session_config=config,
            safety_runtime=self._safety,
            model_runtime=ProviderNeutralModelRuntime(
                model_port=model,
                provider_manifest=manifest,
                model_name=model.model_name,
            ),
            draft_gate=EthicalDraftGate(self._output_policy),
            ledger=self._runtime,
        )

    @staticmethod
    def _session_config(request: CreateSessionRequestV1) -> SessionConfig:
        return SessionConfig(
            contract_version="v1",
            scenario_id=request.scenario_id,
            locale=request.locale,
            plugin_profile_id=request.plugin_profile_id,
        )

    def _owned_session(
        self, session_id: str, identity: IdentityContextV1
    ) -> StoredResearchSessionV1:
        stored = self._web.load_session(session_id)
        self._require_owner(stored.owner_subject, identity)
        return stored

    @staticmethod
    def _require_owner(owner: str, identity: IdentityContextV1) -> None:
        if identity.role is not IdentityRole.PARTICIPANT or identity.subject != owner:
            raise PermissionError("participant does not own this synthetic session")

    def _aware_now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("clock must return a timezone-aware datetime")
        return value

    @staticmethod
    def _validate_idempotency_key(value: str) -> None:
        if not value.strip():
            raise ValueError("idempotency key must not be blank")

    @staticmethod
    def _request_hash(key: str, request: BaseModel, identity: IdentityContextV1) -> str:
        payload = request.model_dump(mode="json")
        return canonical_sha256(
            {"idempotency_key": key, "request": payload, "subject": identity.subject}
        )

    @staticmethod
    def _turn_public_outcome(
        status: SyntheticTurnStatus,
    ) -> tuple[PublicSessionStateV1, ReleaseDispositionV1, SseEventTypeV1]:
        if status is SyntheticTurnStatus.RELEASED:
            return (
                PublicSessionStateV1.ANSWER_AVAILABLE,
                ReleaseDispositionV1.ALLOW,
                SseEventTypeV1.ANSWER_RELEASED,
            )
        if status is SyntheticTurnStatus.FAILED_CLOSED:
            return (
                PublicSessionStateV1.FAILED_CLOSED,
                ReleaseDispositionV1.SYSTEM_FAILURE,
                SseEventTypeV1.FAILED_CLOSED,
            )
        return (
            PublicSessionStateV1.REVIEW_PENDING,
            ReleaseDispositionV1.HOLD_FOR_REVIEW,
            SseEventTypeV1.REVIEW_REQUIRED,
        )

    @staticmethod
    def _public_event(
        participant: ParticipantSessionV1,
        *,
        sequence: int,
        event_type: SseEventTypeV1,
        released_turn: Turn | None = None,
    ) -> SseEventV1:
        return SseEventV1(
            contract_version="v1",
            event_id=f"{participant.session_id}:public:{sequence}",
            session_id=participant.session_id,
            sequence=sequence,
            event_type=event_type,
            public_state=participant.public_state,
            release_disposition=participant.release_disposition,
            released_turn=released_turn,
        )

    @staticmethod
    def _summary(participant: ParticipantSessionV1) -> ParticipantSummaryV1:
        chinese = participant.locale == "zh-CN"
        return ParticipantSummaryV1(
            contract_version="v1",
            session_id=participant.session_id,
            locale=participant.locale,
            title="研究演示摘要" if chinese else "Research demonstration summary",
            summary=(
                "本次成人合成角色扮演研究会话已结束。"
                if chinese
                else "This adult synthetic role-play research session is closed."
            ),
            released_turns=participant.released_turns,
            disclosure=(
                "这不是治疗、诊断、危机照护或紧急服务；模拟审核队列并非有人值守。"
                if chinese
                else "Not therapy, diagnosis, crisis care, or an emergency service; "
                "the simulated review queue is not staffed care."
            ),
        )

    def _ensure_local_profile(self) -> None:
        critical = (
            ("provider-local-deterministic", PluginKind.MODEL_PROVIDER),
            ("input-safety-v1", PluginKind.INPUT_SAFETY_DETECTOR),
            ("output-guard-v1", PluginKind.OUTPUT_GUARD),
            ("resource-catalog-v1", PluginKind.RESOURCE_CATALOG),
        )
        profile = PluginProfileV1(
            contract_version="v1",
            profile_id="profile-local-v1",
            profile_version="v1",
            plugins=tuple(
                PluginProfileEntryV1(
                    contract_version="v1",
                    plugin_id=plugin_id,
                    plugin_version="v1",
                    kind=kind,
                    enabled=True,
                    locked=True,
                    configuration={},
                )
                for plugin_id, kind in critical
            ),
        )
        self._runtime.save_plugin_profile(profile)
