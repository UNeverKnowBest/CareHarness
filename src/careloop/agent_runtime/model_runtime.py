"""Provider-neutral, fail-closed generation of quarantined model drafts."""

from enum import StrEnum
from typing import Self

from pydantic import ValidationError, model_validator

from careloop.agent_runtime.contracts import (
    ContractVersion,
    ModelDraft,
    ModelRequest,
    NonBlankStr,
    PluginFailureMode,
    PluginKind,
    PluginManifestV1,
    RuntimeContractModel,
    SessionState,
)
from careloop.agent_runtime.ports import ModelPort
from careloop.agent_runtime.state_machine import (
    RuntimeEvent,
    SessionEvent,
)


class ModelRuntimeFailureCode(StrEnum):
    """Stable non-sensitive categories for provider-boundary failures."""

    PROVIDER_EXCEPTION = "provider_exception"
    INVALID_DRAFT = "invalid_draft"
    REQUEST_MISMATCH = "request_mismatch"
    PROVIDER_MISMATCH = "provider_mismatch"
    MODEL_MISMATCH = "model_mismatch"


class ModelRuntimeResult(RuntimeContractModel):
    """A quarantined draft or a typed fail-closed transition, never a reply."""

    contract_version: ContractVersion
    request_id: NonBlankStr
    event: RuntimeEvent
    quarantined_draft: ModelDraft | None
    failure_code: ModelRuntimeFailureCode | None

    @model_validator(mode="after")
    def validate_result_shape(self) -> Self:
        if self.event.causation_id != self.request_id:
            raise ValueError("event causation_id must equal request_id")
        if self.failure_code is None:
            if self.quarantined_draft is None:
                raise ValueError("successful generation requires quarantined_draft")
            if self.event.event is not SessionEvent.DRAFT_GENERATED:
                raise ValueError("successful generation requires DRAFT_GENERATED")
            if self.quarantined_draft.request_id != self.request_id:
                raise ValueError("quarantined_draft request_id must match result")
            if self.event.evidence_ids != (self.quarantined_draft.draft_id,):
                raise ValueError(
                    "successful generation evidence_ids must contain only draft_id"
                )
        else:
            if self.quarantined_draft is not None:
                raise ValueError("failed generation cannot retain a draft")
            if self.event.event is not SessionEvent.RUNTIME_FAILURE:
                raise ValueError("failed generation requires RUNTIME_FAILURE")
            expected_evidence = (f"model_runtime:{self.failure_code.value}",)
            if self.event.evidence_ids != expected_evidence:
                raise ValueError(
                    "failed generation evidence_ids must contain only failure_code"
                )
        return self


class ProviderNeutralModelRuntime:
    """Invoke one injected model port and keep its complete response quarantined."""

    def __init__(
        self,
        *,
        model_port: ModelPort,
        provider_manifest: PluginManifestV1,
        model_name: str,
    ) -> None:
        if provider_manifest.kind is not PluginKind.MODEL_PROVIDER:
            raise ValueError("provider_manifest must have kind model_provider")
        if provider_manifest.failure_mode is not PluginFailureMode.CRITICAL_FAIL_CLOSED:
            raise ValueError("model_provider must be critical_fail_closed")
        if not model_name.strip():
            raise ValueError("model_name must not be empty or whitespace")
        self._model_port = model_port
        self._provider_id = provider_manifest.plugin_id
        self._model_name = model_name

    async def generate(
        self,
        request: ModelRequest,
        *,
        event_id: str,
        event_sequence: int,
    ) -> ModelRuntimeResult:
        try:
            raw_draft: object = await self._model_port.generate(request)
        except Exception:
            return self._failed(
                request,
                event_id=event_id,
                event_sequence=event_sequence,
                code=ModelRuntimeFailureCode.PROVIDER_EXCEPTION,
            )

        try:
            draft_input = (
                raw_draft.model_dump()
                if isinstance(raw_draft, ModelDraft)
                else raw_draft
            )
            draft = ModelDraft.model_validate(draft_input)
        except (ValidationError, TypeError, ValueError):
            return self._failed(
                request,
                event_id=event_id,
                event_sequence=event_sequence,
                code=ModelRuntimeFailureCode.INVALID_DRAFT,
            )
        if draft.request_id != request.request_id:
            code = ModelRuntimeFailureCode.REQUEST_MISMATCH
        elif draft.provider_id != self._provider_id:
            code = ModelRuntimeFailureCode.PROVIDER_MISMATCH
        elif draft.model_name != self._model_name:
            code = ModelRuntimeFailureCode.MODEL_MISMATCH
        else:
            return self._succeeded(
                request,
                draft=draft,
                event_id=event_id,
                event_sequence=event_sequence,
            )
        return self._failed(
            request,
            event_id=event_id,
            event_sequence=event_sequence,
            code=code,
        )

    @staticmethod
    def _succeeded(
        request: ModelRequest,
        *,
        draft: ModelDraft,
        event_id: str,
        event_sequence: int,
    ) -> ModelRuntimeResult:
        event = RuntimeEvent(
            contract_version="v1",
            event_id=event_id,
            session_id=request.session_id,
            sequence=event_sequence,
            event=SessionEvent.DRAFT_GENERATED,
            state_before=SessionState.DRAFTING,
            state_after=SessionState.CHECKING_DRAFT,
            causation_id=request.request_id,
            evidence_ids=(draft.draft_id,),
        )
        return ModelRuntimeResult(
            contract_version="v1",
            request_id=request.request_id,
            event=event,
            quarantined_draft=draft,
            failure_code=None,
        )

    @staticmethod
    def _failed(
        request: ModelRequest,
        *,
        event_id: str,
        event_sequence: int,
        code: ModelRuntimeFailureCode,
    ) -> ModelRuntimeResult:
        event = RuntimeEvent(
            contract_version="v1",
            event_id=event_id,
            session_id=request.session_id,
            sequence=event_sequence,
            event=SessionEvent.RUNTIME_FAILURE,
            state_before=SessionState.DRAFTING,
            state_after=SessionState.FAILED_CLOSED,
            causation_id=request.request_id,
            evidence_ids=(f"model_runtime:{code.value}",),
        )
        return ModelRuntimeResult(
            contract_version="v1",
            request_id=request.request_id,
            event=event,
            quarantined_draft=None,
            failure_code=code,
        )
