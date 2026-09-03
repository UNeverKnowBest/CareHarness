from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from careloop.web_api.contracts import (
    CloseSessionRequestV1,
    CreateSessionRequestV1,
    PublicSessionStateV1,
    ReleaseDispositionV1,
    SubmitTurnRequestV1,
)
from careloop.web_api.demo_service import LocalResearchService
from careloop.web_api.identity import IdentityContextV1, IdentityRole

ROOT = Path(__file__).parents[2]
NOW = datetime(2026, 9, 3, 12, tzinfo=UTC)


def _service() -> LocalResearchService:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return LocalResearchService(
        engine=engine,
        repository_root=ROOT,
        clock=lambda: NOW,
    )


def _participant() -> IdentityContextV1:
    return IdentityContextV1(
        contract_version="v1",
        subject="synthetic-local:participant-1",
        role=IdentityRole.PARTICIPANT,
        auth_source="local_synthetic",
    )


def _other_participant() -> IdentityContextV1:
    return IdentityContextV1(
        contract_version="v1",
        subject="synthetic-local:participant-2",
        role=IdentityRole.PARTICIPANT,
        auth_source="local_synthetic",
    )


def _create(session_id: str) -> CreateSessionRequestV1:
    return CreateSessionRequestV1(
        contract_version="v1",
        session_id=session_id,
        scenario_id="seed-support-en-v1",
        locale="en-US",
        model_id="deterministic-demo-v1",
        policy_version="v1",
        plugin_profile_id="profile-local-v1",
        evidence_registry_version="v1",
        adult_synthetic_role_play=True,
    )


def test_local_service_drives_real_input_route_gate_and_atomic_public_event() -> None:
    service = _service()
    identity = _participant()
    created = service.create_session(
        _create("session-safe"),
        idempotency_key="create-safe",
        identity=identity,
    )
    assert created.public_state is PublicSessionStateV1.READY

    released = service.submit_turn(
        "session-safe",
        SubmitTurnRequestV1(
            contract_version="v1",
            request_id="request-safe",
            turn_id="turn-safe-user",
            sequence=0,
            text="[SYNTHETIC] I am rehearsing a fictional work transition.",
        ),
        idempotency_key="request-safe",
        identity=identity,
    )

    assert released.release_disposition is ReleaseDispositionV1.ALLOW
    assert len(released.released_turns) == 1
    events = tuple(
        service.stream_events("session-safe", after_event_id=None, identity=identity)
    )
    assert events[-1].released_turn == released.released_turns[-1]
    assert all("draft" not in item.model_dump_json().casefold() for item in events)


def test_local_service_suppresses_synthetic_override_without_model_answer() -> None:
    service = _service()
    identity = _participant()
    service.create_session(
        _create("session-override"),
        idempotency_key="create-override",
        identity=identity,
    )
    held = service.submit_turn(
        "session-override",
        SubmitTurnRequestV1(
            contract_version="v1",
            request_id="request-override",
            turn_id="turn-override-user",
            sequence=0,
            text="[SYNTHETIC SAFETY SIGNAL: CURRENT PLAN] Fictional fixture.",
        ),
        idempotency_key="request-override",
        identity=identity,
    )

    assert held.release_disposition is ReleaseDispositionV1.HOLD_FOR_REVIEW
    assert held.released_turns == ()
    event = tuple(
        service.stream_events(
            "session-override", after_event_id=None, identity=identity
        )
    )[-1]
    assert event.released_turn is None


def test_close_runs_existing_evaluator_and_persists_canonical_report() -> None:
    service = _service()
    identity = _participant()
    service.create_session(
        _create("session-close"),
        idempotency_key="create-close",
        identity=identity,
    )
    service.submit_turn(
        "session-close",
        SubmitTurnRequestV1(
            contract_version="v1",
            request_id="request-close-turn",
            turn_id="turn-close-user",
            sequence=0,
            text="[SYNTHETIC] Fictional support rehearsal.",
        ),
        idempotency_key="request-close-turn",
        identity=identity,
    )
    closed = service.close_session(
        "session-close",
        CloseSessionRequestV1(
            contract_version="v1",
            request_id="request-close",
            trajectory_id="trajectory-session-close",
            evidence_ids=("m16-local-close",),
        ),
        idempotency_key="request-close",
        identity=identity,
    )

    assert closed.public_state is PublicSessionStateV1.CLOSED
    report = service.get_report("session-close", identity=identity)
    assert report.participant_summary.released_turns == closed.released_turns
    assert report.evidence["evaluation"]
    recovered = service.get_session("session-close", identity=identity)
    assert recovered == closed


def test_create_idempotency_returns_original_projection_after_session_progress() -> (
    None
):
    service = _service()
    identity = _participant()
    request = _create("session-create-retry")
    created = service.create_session(
        request,
        idempotency_key="create-retry",
        identity=identity,
    )
    service.submit_turn(
        request.session_id,
        SubmitTurnRequestV1(
            contract_version="v1",
            request_id="request-after-create",
            turn_id="turn-after-create",
            sequence=0,
            text="[SYNTHETIC] Fictional rehearsal.",
        ),
        idempotency_key="turn-after-create",
        identity=identity,
    )

    retried = service.create_session(
        request,
        idempotency_key="create-retry",
        identity=identity,
    )

    assert retried == created


def test_create_rejects_existing_session_identity_from_another_participant() -> None:
    service = _service()
    request = _create("session-owned")
    service.create_session(
        request,
        idempotency_key="create-owner",
        identity=_participant(),
    )

    with pytest.raises(PermissionError):
        service.create_session(
            request,
            idempotency_key="create-other",
            identity=_other_participant(),
        )
