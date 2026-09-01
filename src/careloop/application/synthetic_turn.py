"""Deterministic M10 orchestration for one synthetic role-play turn."""

from datetime import date
from enum import StrEnum
from typing import Protocol, Self

from pydantic import BaseModel, ConfigDict, model_validator

from careloop.agent_runtime import (
    MAX_DRAFT_REWRITE_ATTEMPTS,
    DraftDecision,
    DraftGateResult,
    ModelDraft,
    ModelRequest,
    ProviderNeutralModelRuntime,
    RuntimeEvent,
    RuntimeEventLedgerPort,
    SafetyDisposition,
    SessionConfig,
    SessionEvent,
    SessionState,
    transition_session,
)
from careloop.agent_runtime.contracts import ContractVersion, NonBlankStr, Sha256Digest
from careloop.domain import CrisisResource, SafetyEvent, Turn
from careloop.safety.output_policy import EthicalOutputDecision
from careloop.safety.runtime import SafetyRuntimeResult, SafetyRuntimeStatus


class SyntheticTurnStatus(StrEnum):
    """Participant-safe outcomes of one synthetic command."""

    RELEASED = "released"
    OVERRIDE_SUPPRESSED = "override_suppressed"
    AWAITING_HUMAN_REVIEW = "awaiting_human_review"
    FAILED_CLOSED = "failed_closed"


class SyntheticTurnFailureCode(StrEnum):
    """Stable application failure categories without exception details."""

    INPUT_SAFETY_FAILURE = "input_safety_failure"
    MODEL_RUNTIME_FAILURE = "model_runtime_failure"
    DRAFT_GATE_FAILURE = "draft_gate_failure"
    LEDGER_FAILURE = "ledger_failure"


class SyntheticTurnContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class SyntheticTurnCommand(SyntheticTurnContractModel):
    """Strict explicit inputs for one synthetic role-play turn."""

    contract_version: ContractVersion
    request_id: NonBlankStr
    input_turn: Turn
    context_turns: tuple[Turn, ...]
    jurisdiction: str | None
    as_of: date
    prompt_template_id: NonBlankStr
    prompt_template_hash: Sha256Digest

    @model_validator(mode="after")
    def validate_model_context(self) -> Self:
        ModelRequest(
            contract_version=self.contract_version,
            request_id=self.request_id,
            session_id="synthetic-command-validation",
            input_turn=self.input_turn,
            context_turns=self.context_turns,
            locale="synthetic-command-validation",
            prompt_template_id=self.prompt_template_id,
            prompt_template_hash=self.prompt_template_hash,
        )
        return self


class ParticipantTurnView(SyntheticTurnContractModel):
    """Participant projection with released or override evidence only."""

    contract_version: ContractVersion
    request_id: NonBlankStr
    session_id: NonBlankStr
    status: SyntheticTurnStatus
    state: SessionState
    released_turn: Turn | None
    safety_event: SafetyEvent | None
    resources: tuple[CrisisResource, ...]

    @model_validator(mode="after")
    def validate_projection(self) -> Self:
        if self.status is SyntheticTurnStatus.RELEASED:
            if self.state is not SessionState.RESPONSE_RELEASED:
                raise ValueError("released status requires RESPONSE_RELEASED")
            if self.released_turn is None or self.released_turn.role != "assistant":
                raise ValueError("released status requires one assistant turn")
            if self.safety_event is not None:
                raise ValueError("released status cannot contain a safety override")
        else:
            if self.released_turn is not None:
                raise ValueError("only released status may contain released_turn")
        if self.status is SyntheticTurnStatus.OVERRIDE_SUPPRESSED:
            if self.safety_event is None:
                raise ValueError("override_suppressed requires safety_event")
            if not self.safety_event.normal_flow_suppressed:
                raise ValueError("override_suppressed requires normal-flow suppression")
            if self.state not in {
                SessionState.ACTIVE,
                SessionState.RESPONSE_RELEASED,
            }:
                raise ValueError("override_suppressed requires a runnable state")
        if (
            self.status is SyntheticTurnStatus.AWAITING_HUMAN_REVIEW
            and self.state is not SessionState.AWAITING_HUMAN_REVIEW
        ):
            raise ValueError("awaiting_human_review status requires matching state")
        if (
            self.status is SyntheticTurnStatus.FAILED_CLOSED
            and self.state is not SessionState.FAILED_CLOSED
        ):
            raise ValueError("failed_closed status requires matching state")
        return self


class ResearchReviewTurnView(SyntheticTurnContractModel):
    """Reviewer projection retaining quarantined evidence and runtime events."""

    contract_version: ContractVersion
    participant: ParticipantTurnView
    quarantined_drafts: tuple[ModelDraft, ...]
    draft_gate_results: tuple[DraftGateResult, ...]
    runtime_events: tuple[RuntimeEvent, ...]
    failure_code: SyntheticTurnFailureCode | None

    @model_validator(mode="after")
    def validate_failure_shape(self) -> Self:
        failed = self.participant.status is SyntheticTurnStatus.FAILED_CLOSED
        if failed != (self.failure_code is not None):
            raise ValueError("failure_code must exist exactly for failed_closed")
        if any(
            event.session_id != self.participant.session_id
            for event in self.runtime_events
        ):
            raise ValueError("runtime_events must belong to participant session")
        return self


class IdempotencyConflict(ValueError):
    """Raised when one request identity is reused with changed content."""


class SessionNotRunnable(ValueError):
    """Raised when a participant command attempts to bypass a terminal/hold state."""


class RuntimeLedgerUnavailable(RuntimeError):
    """Raised when even the failed-closed event cannot be appended."""


class InputSafetyRuntime(Protocol):
    def route_input(
        self,
        turn: Turn,
        *,
        jurisdiction: str | None,
        as_of: date,
    ) -> SafetyRuntimeResult | None: ...


class DraftGate(Protocol):
    def check(
        self,
        draft: ModelDraft,
        *,
        input_turn: Turn,
        rewrite_count: int,
    ) -> DraftGateResult: ...


class OutputPolicy(Protocol):
    def evaluate(
        self,
        output: Turn,
        *,
        override_active: bool,
    ) -> EthicalOutputDecision: ...


class EthicalDraftGate:
    """Map the existing deterministic ethical policy to the M8 draft gate."""

    def __init__(self, output_policy: OutputPolicy) -> None:
        self._output_policy = output_policy

    def check(
        self,
        draft: ModelDraft,
        *,
        input_turn: Turn,
        rewrite_count: int,
    ) -> DraftGateResult:
        output = Turn(
            turn_id=f"{input_turn.turn_id}:assistant:draft:{rewrite_count}",
            sequence=input_turn.sequence + 1,
            role="assistant",
            text=draft.text,
        )
        decision = self._output_policy.evaluate(output, override_active=False)
        finding_ids = tuple(finding.finding_id for finding in decision.findings)
        if decision.allowed:
            gate_decision = DraftDecision.ALLOW
            disposition = SafetyDisposition.SUPPORT_ALLOWED
        elif rewrite_count < MAX_DRAFT_REWRITE_ATTEMPTS:
            gate_decision = DraftDecision.REWRITE
            disposition = SafetyDisposition.CLARIFICATION_REQUIRED
        else:
            gate_decision = DraftDecision.HOLD_FOR_REVIEW
            disposition = SafetyDisposition.HUMAN_REVIEW_REQUIRED
        return DraftGateResult(
            contract_version="v1",
            draft_id=draft.draft_id,
            decision=gate_decision,
            disposition=disposition,
            rewrite_count=rewrite_count,
            finding_ids=finding_ids,
        )


class RunSyntheticTurn:
    """Run one synthetic turn with input-first routing and atomic release."""

    def __init__(
        self,
        *,
        session_id: str,
        session_config: SessionConfig,
        safety_runtime: InputSafetyRuntime,
        model_runtime: ProviderNeutralModelRuntime,
        draft_gate: DraftGate,
        ledger: RuntimeEventLedgerPort,
    ) -> None:
        if not session_id.strip():
            raise ValueError("session_id must not be empty or whitespace")
        self._session_id = session_id
        self._session_config = SessionConfig.model_validate(session_config.model_dump())
        self._safety_runtime = safety_runtime
        self._model_runtime = model_runtime
        self._draft_gate = draft_gate
        self._ledger = ledger
        self._ledger.bind_session(session_id, self._session_config)
        self._results: dict[
            str, tuple[SyntheticTurnCommand, ResearchReviewTurnView]
        ] = {}

    async def execute(self, command: SyntheticTurnCommand) -> ResearchReviewTurnView:
        command = SyntheticTurnCommand.model_validate(command.model_dump())
        cached = self._results.get(command.request_id)
        if cached is not None:
            prior_command, prior_result = cached
            if prior_command != command:
                raise IdempotencyConflict(
                    f"request_id {command.request_id!r} has conflicting content"
                )
            return ResearchReviewTurnView.model_validate(prior_result.model_dump())

        first_event_index = len(self._ledger.events_for(self._session_id))
        if self._ledger.state_for(self._session_id) is SessionState.CREATED:
            start = self._event(
                command,
                suffix="start",
                event=SessionEvent.START_SESSION,
                before=SessionState.CREATED,
                causation_id=f"{self._session_id}:create",
                evidence_ids=(
                    self._session_config.scenario_id,
                    self._session_config.plugin_profile_id,
                ),
            )
            failure = self._append_or_ledger_failure(
                command,
                start,
                first_event_index=first_event_index,
            )
            if failure is not None:
                return self._remember(command, failure)

        state = self._ledger.state_for(self._session_id)
        if state not in {SessionState.ACTIVE, SessionState.RESPONSE_RELEASED}:
            raise SessionNotRunnable(
                f"session {self._session_id!r} is not runnable from {state.value}"
            )

        try:
            routed = self._safety_runtime.route_input(
                command.input_turn,
                jurisdiction=command.jurisdiction,
                as_of=command.as_of,
            )
        except Exception:
            result = self._fail_closed(
                command,
                SyntheticTurnFailureCode.INPUT_SAFETY_FAILURE,
                first_event_index=first_event_index,
            )
            return self._remember(command, result)
        if routed is not None:
            if routed.status is not SafetyRuntimeStatus.CRISIS_OVERRIDE:
                result = self._fail_closed(
                    command,
                    SyntheticTurnFailureCode.INPUT_SAFETY_FAILURE,
                    first_event_index=first_event_index,
                    safety_result=routed,
                )
            else:
                result = self._result(
                    command,
                    status=SyntheticTurnStatus.OVERRIDE_SUPPRESSED,
                    first_event_index=first_event_index,
                    safety_result=routed,
                )
            return self._remember(command, result)

        submitted = self._event(
            command,
            suffix="submit",
            event=SessionEvent.SUBMIT_TURN,
            before=state,
            causation_id=command.request_id,
            evidence_ids=(command.input_turn.turn_id,),
        )
        failure = self._append_or_ledger_failure(
            command,
            submitted,
            first_event_index=first_event_index,
        )
        if failure is not None:
            return self._remember(command, failure)

        drafts: list[ModelDraft] = []
        gate_results: list[DraftGateResult] = []
        rewrite_count = 0
        while True:
            model_request = ModelRequest(
                contract_version="v1",
                request_id=(
                    f"{self._session_id}:{command.request_id}:model:{rewrite_count}"
                ),
                session_id=self._session_id,
                input_turn=command.input_turn,
                context_turns=command.context_turns,
                locale=self._session_config.locale,
                prompt_template_id=command.prompt_template_id,
                prompt_template_hash=command.prompt_template_hash,
            )
            model_result = await self._model_runtime.generate(
                model_request,
                event_id=(
                    f"{self._session_id}:{command.request_id}:draft:{rewrite_count}"
                ),
                event_sequence=self._ledger.next_sequence(self._session_id),
            )
            model_event_failure = self._append_or_ledger_failure(
                command,
                model_result.event,
                first_event_index=first_event_index,
                drafts=tuple(drafts),
                gate_results=tuple(gate_results),
            )
            if model_event_failure is not None:
                return self._remember(command, model_event_failure)
            if model_result.failure_code is not None:
                result = self._result(
                    command,
                    status=SyntheticTurnStatus.FAILED_CLOSED,
                    first_event_index=first_event_index,
                    drafts=tuple(drafts),
                    gate_results=tuple(gate_results),
                    failure_code=SyntheticTurnFailureCode.MODEL_RUNTIME_FAILURE,
                )
                return self._remember(command, result)
            draft = model_result.quarantined_draft
            if draft is None:
                result = self._fail_closed(
                    command,
                    SyntheticTurnFailureCode.MODEL_RUNTIME_FAILURE,
                    first_event_index=first_event_index,
                    drafts=tuple(drafts),
                    gate_results=tuple(gate_results),
                )
                return self._remember(command, result)
            drafts.append(draft)

            try:
                raw_gate = self._draft_gate.check(
                    draft,
                    input_turn=command.input_turn,
                    rewrite_count=rewrite_count,
                )
                gate = DraftGateResult.model_validate(raw_gate.model_dump())
                if gate.draft_id != draft.draft_id:
                    raise ValueError("draft gate result has mismatched draft_id")
                if gate.rewrite_count != rewrite_count:
                    raise ValueError("draft gate result has mismatched rewrite_count")
            except Exception:
                result = self._fail_closed(
                    command,
                    SyntheticTurnFailureCode.DRAFT_GATE_FAILURE,
                    first_event_index=first_event_index,
                    drafts=tuple(drafts),
                    gate_results=tuple(gate_results),
                )
                return self._remember(command, result)
            gate_results.append(gate)

            if gate.decision is DraftDecision.ALLOW:
                approved = self._gate_event(
                    command,
                    gate,
                    SessionEvent.DRAFT_APPROVED,
                )
                failure = self._append_or_ledger_failure(
                    command,
                    approved,
                    first_event_index=first_event_index,
                    drafts=tuple(drafts),
                    gate_results=tuple(gate_results),
                )
                if failure is not None:
                    return self._remember(command, failure)
                released = Turn(
                    turn_id=f"{command.input_turn.turn_id}:assistant",
                    sequence=command.input_turn.sequence + 1,
                    role="assistant",
                    text=draft.text,
                )
                result = self._result(
                    command,
                    status=SyntheticTurnStatus.RELEASED,
                    first_event_index=first_event_index,
                    released_turn=released,
                    drafts=tuple(drafts),
                    gate_results=tuple(gate_results),
                )
                return self._remember(command, result)

            if gate.decision is DraftDecision.REWRITE:
                rewrite = self._gate_event(
                    command,
                    gate,
                    SessionEvent.DRAFT_REWRITE_REQUESTED,
                )
                failure = self._append_or_ledger_failure(
                    command,
                    rewrite,
                    first_event_index=first_event_index,
                    drafts=tuple(drafts),
                    gate_results=tuple(gate_results),
                )
                if failure is not None:
                    return self._remember(command, failure)
                rewrite_count += 1
                continue

            held = self._gate_event(
                command,
                gate,
                SessionEvent.DRAFT_HELD_FOR_REVIEW,
            )
            failure = self._append_or_ledger_failure(
                command,
                held,
                first_event_index=first_event_index,
                drafts=tuple(drafts),
                gate_results=tuple(gate_results),
            )
            if failure is not None:
                return self._remember(command, failure)
            result = self._result(
                command,
                status=SyntheticTurnStatus.AWAITING_HUMAN_REVIEW,
                first_event_index=first_event_index,
                drafts=tuple(drafts),
                gate_results=tuple(gate_results),
            )
            return self._remember(command, result)

    def _event(
        self,
        command: SyntheticTurnCommand,
        *,
        suffix: str,
        event: SessionEvent,
        before: SessionState,
        causation_id: str,
        evidence_ids: tuple[str, ...],
    ) -> RuntimeEvent:
        return RuntimeEvent(
            contract_version="v1",
            event_id=f"{self._session_id}:{command.request_id}:{suffix}",
            session_id=self._session_id,
            sequence=self._ledger.next_sequence(self._session_id),
            event=event,
            state_before=before,
            state_after=self._transition_after(before, event),
            causation_id=causation_id,
            evidence_ids=evidence_ids,
        )

    def _gate_event(
        self,
        command: SyntheticTurnCommand,
        gate: DraftGateResult,
        event: SessionEvent,
    ) -> RuntimeEvent:
        return self._event(
            command,
            suffix=f"gate:{gate.rewrite_count}:{event.value.casefold()}",
            event=event,
            before=SessionState.CHECKING_DRAFT,
            causation_id=gate.draft_id,
            evidence_ids=(gate.draft_id,) + gate.finding_ids,
        )

    @staticmethod
    def _transition_after(before: SessionState, event: SessionEvent) -> SessionState:
        return transition_session(before, event)

    def _append_or_ledger_failure(
        self,
        command: SyntheticTurnCommand,
        event: RuntimeEvent,
        *,
        first_event_index: int,
        drafts: tuple[ModelDraft, ...] = (),
        gate_results: tuple[DraftGateResult, ...] = (),
    ) -> ResearchReviewTurnView | None:
        try:
            self._ledger.append(event)
        except Exception:
            return self._fail_closed(
                command,
                SyntheticTurnFailureCode.LEDGER_FAILURE,
                first_event_index=first_event_index,
                drafts=drafts,
                gate_results=gate_results,
            )
        return None

    def _fail_closed(
        self,
        command: SyntheticTurnCommand,
        code: SyntheticTurnFailureCode,
        *,
        first_event_index: int,
        safety_result: SafetyRuntimeResult | None = None,
        drafts: tuple[ModelDraft, ...] = (),
        gate_results: tuple[DraftGateResult, ...] = (),
    ) -> ResearchReviewTurnView:
        before = self._ledger.state_for(self._session_id)
        failure = self._event(
            command,
            suffix=f"failure:{code.value}",
            event=SessionEvent.RUNTIME_FAILURE,
            before=before,
            causation_id=command.request_id,
            evidence_ids=(f"synthetic_turn:{code.value}",),
        )
        try:
            self._ledger.append(failure)
        except Exception as error:
            raise RuntimeLedgerUnavailable(
                "failed-closed event could not be appended; no output was released"
            ) from error
        return self._result(
            command,
            status=SyntheticTurnStatus.FAILED_CLOSED,
            first_event_index=first_event_index,
            safety_result=safety_result,
            drafts=drafts,
            gate_results=gate_results,
            failure_code=code,
        )

    def _result(
        self,
        command: SyntheticTurnCommand,
        *,
        status: SyntheticTurnStatus,
        first_event_index: int,
        safety_result: SafetyRuntimeResult | None = None,
        released_turn: Turn | None = None,
        drafts: tuple[ModelDraft, ...] = (),
        gate_results: tuple[DraftGateResult, ...] = (),
        failure_code: SyntheticTurnFailureCode | None = None,
    ) -> ResearchReviewTurnView:
        participant = ParticipantTurnView(
            contract_version="v1",
            request_id=command.request_id,
            session_id=self._session_id,
            status=status,
            state=self._ledger.state_for(self._session_id),
            released_turn=released_turn,
            safety_event=None if safety_result is None else safety_result.event,
            resources=() if safety_result is None else safety_result.resources,
        )
        return ResearchReviewTurnView(
            contract_version="v1",
            participant=participant,
            quarantined_drafts=drafts,
            draft_gate_results=gate_results,
            runtime_events=self._ledger.events_for(self._session_id)[
                first_event_index:
            ],
            failure_code=failure_code,
        )

    def _remember(
        self,
        command: SyntheticTurnCommand,
        result: ResearchReviewTurnView,
    ) -> ResearchReviewTurnView:
        command_snapshot = SyntheticTurnCommand.model_validate(command.model_dump())
        result_snapshot = ResearchReviewTurnView.model_validate(result.model_dump())
        self._results[command.request_id] = (command_snapshot, result_snapshot)
        return ResearchReviewTurnView.model_validate(result_snapshot.model_dump())
