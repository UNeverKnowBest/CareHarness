import pytest

from careloop.agent_runtime import (
    RuntimeEvent,
    SessionConfig,
    SessionEvent,
    SessionState,
)
from careloop.runtime_storage import (
    InMemoryRuntimeEventLedger,
    LedgerAppendError,
    SessionConfigConflict,
)


def _config(profile: str = "profile-synthetic-default") -> SessionConfig:
    return SessionConfig(
        contract_version="v1",
        scenario_id="scenario-synthetic-001",
        locale="en",
        plugin_profile_id=profile,
    )


def _event(
    *,
    event_id: str,
    session_id: str = "session-001",
    sequence: int,
    event: SessionEvent,
    before: SessionState,
    after: SessionState,
) -> RuntimeEvent:
    return RuntimeEvent(
        contract_version="v1",
        event_id=event_id,
        session_id=session_id,
        sequence=sequence,
        event=event,
        state_before=before,
        state_after=after,
        causation_id=f"cause:{event_id}",
        evidence_ids=(),
    )


def test_ledger_binds_immutable_session_configuration() -> None:
    ledger = InMemoryRuntimeEventLedger()

    ledger.bind_session("session-001", _config())
    ledger.bind_session("session-001", _config())

    with pytest.raises(SessionConfigConflict, match="session configuration"):
        ledger.bind_session("session-001", _config("profile-other"))


def test_ledger_appends_contiguous_events_and_reconstructs_state() -> None:
    ledger = InMemoryRuntimeEventLedger()
    ledger.bind_session("session-001", _config())
    started = _event(
        event_id="event-start",
        sequence=0,
        event=SessionEvent.START_SESSION,
        before=SessionState.CREATED,
        after=SessionState.ACTIVE,
    )
    submitted = _event(
        event_id="event-submit",
        sequence=1,
        event=SessionEvent.SUBMIT_TURN,
        before=SessionState.ACTIVE,
        after=SessionState.DRAFTING,
    )

    ledger.append(started)
    ledger.append(submitted)

    assert ledger.events_for("session-001") == (started, submitted)
    assert ledger.state_for("session-001") is SessionState.DRAFTING
    assert ledger.next_sequence("session-001") == 2
    assert not hasattr(ledger, "update")
    assert not hasattr(ledger, "delete")

    returned = ledger.events_for("session-001")
    returned[0].event_id = "mutated-outside-ledger"
    assert ledger.events_for("session-001")[0].event_id == "event-start"


@pytest.mark.parametrize("invalid", ["skip", "state", "session"])
def test_ledger_rejects_invalid_append_without_mutating_snapshot(invalid: str) -> None:
    ledger = InMemoryRuntimeEventLedger()
    ledger.bind_session("session-001", _config())
    started = _event(
        event_id="event-start",
        sequence=0,
        event=SessionEvent.START_SESSION,
        before=SessionState.CREATED,
        after=SessionState.ACTIVE,
    )
    ledger.append(started)
    before = ledger.events_for("session-001")

    if invalid == "skip":
        candidate = _event(
            event_id="event-invalid",
            sequence=2,
            event=SessionEvent.SUBMIT_TURN,
            before=SessionState.ACTIVE,
            after=SessionState.DRAFTING,
        )
    elif invalid == "state":
        candidate = _event(
            event_id="event-invalid",
            sequence=1,
            event=SessionEvent.SUBMIT_TURN,
            before=SessionState.RESPONSE_RELEASED,
            after=SessionState.DRAFTING,
        )
    else:
        candidate = _event(
            event_id="event-invalid",
            session_id="session-unbound",
            sequence=0,
            event=SessionEvent.START_SESSION,
            before=SessionState.CREATED,
            after=SessionState.ACTIVE,
        )

    with pytest.raises(LedgerAppendError):
        ledger.append(candidate)

    assert ledger.events_for("session-001") == before


def test_ledger_rejects_duplicate_event_identity_across_sessions() -> None:
    ledger = InMemoryRuntimeEventLedger()
    ledger.bind_session("session-001", _config())
    ledger.bind_session("session-002", _config())
    ledger.append(
        _event(
            event_id="event-shared",
            sequence=0,
            event=SessionEvent.START_SESSION,
            before=SessionState.CREATED,
            after=SessionState.ACTIVE,
        )
    )

    with pytest.raises(LedgerAppendError, match="event_id"):
        ledger.append(
            _event(
                event_id="event-shared",
                session_id="session-002",
                sequence=0,
                event=SessionEvent.START_SESSION,
                before=SessionState.CREATED,
                after=SessionState.ACTIVE,
            )
        )
