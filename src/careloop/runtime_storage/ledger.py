"""Append-only in-memory runtime-event storage for deterministic M10 tests."""

from careloop.agent_runtime import (
    RuntimeEvent,
    SessionConfig,
    SessionState,
)


class LedgerAppendError(ValueError):
    """Raised when an event would violate append-only ledger invariants."""


class SessionConfigConflict(ValueError):
    """Raised when a session is rebound to a different immutable config."""


class InMemoryRuntimeEventLedger:
    """Local append-only adapter with no clock, file, database, or network I/O."""

    def __init__(self) -> None:
        self._configs: dict[str, SessionConfig] = {}
        self._events: dict[str, list[RuntimeEvent]] = {}
        self._event_ids: set[str] = set()

    def bind_session(self, session_id: str, config: SessionConfig) -> None:
        if not session_id.strip():
            raise ValueError("session_id must not be empty or whitespace")
        snapshot = SessionConfig.model_validate(config.model_dump())
        existing = self._configs.get(session_id)
        if existing is not None and existing != snapshot:
            raise SessionConfigConflict(
                f"session configuration is immutable for {session_id!r}"
            )
        if existing is None:
            self._configs[session_id] = snapshot
            self._events[session_id] = []

    def append(self, event: RuntimeEvent) -> None:
        snapshot = RuntimeEvent.model_validate(event.model_dump())
        session_events = self._events.get(snapshot.session_id)
        if session_events is None:
            raise LedgerAppendError(
                f"session {snapshot.session_id!r} must be bound before append"
            )
        if snapshot.event_id in self._event_ids:
            raise LedgerAppendError(f"duplicate event_id: {snapshot.event_id!r}")
        expected_sequence = len(session_events)
        if snapshot.sequence != expected_sequence:
            raise LedgerAppendError(
                f"sequence must be contiguous: expected {expected_sequence}"
            )
        expected_before = (
            SessionState.CREATED
            if not session_events
            else session_events[-1].state_after
        )
        if snapshot.state_before is not expected_before:
            raise LedgerAppendError(
                f"state_before must equal last state: {expected_before.value}"
            )
        session_events.append(snapshot)
        self._event_ids.add(snapshot.event_id)

    def events_for(self, session_id: str) -> tuple[RuntimeEvent, ...]:
        events = self._events.get(session_id)
        if events is None:
            raise LedgerAppendError(f"unknown session: {session_id!r}")
        return tuple(
            RuntimeEvent.model_validate(event.model_dump()) for event in events
        )

    def state_for(self, session_id: str) -> SessionState:
        events = self._events.get(session_id)
        if events is None:
            raise LedgerAppendError(f"unknown session: {session_id!r}")
        return SessionState.CREATED if not events else events[-1].state_after

    def next_sequence(self, session_id: str) -> int:
        events = self._events.get(session_id)
        if events is None:
            raise LedgerAppendError(f"unknown session: {session_id!r}")
        return len(events)
