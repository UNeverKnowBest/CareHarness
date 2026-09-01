"""Dependency-inversion ports for future model adapters."""

from typing import Protocol

from careloop.agent_runtime.contracts import (
    ModelDraft,
    ModelRequest,
    SessionConfig,
    SessionState,
)
from careloop.agent_runtime.state_machine import RuntimeEvent


class ModelPort(Protocol):
    """Provider-neutral asynchronous model generation boundary."""

    async def generate(self, request: ModelRequest) -> ModelDraft: ...


class RuntimeEventLedgerPort(Protocol):
    """Append-only lifecycle evidence required by application orchestration."""

    def bind_session(self, session_id: str, config: SessionConfig) -> None: ...

    def append(self, event: RuntimeEvent) -> None: ...

    def events_for(self, session_id: str) -> tuple[RuntimeEvent, ...]: ...

    def state_for(self, session_id: str) -> SessionState: ...

    def next_sequence(self, session_id: str) -> int: ...
