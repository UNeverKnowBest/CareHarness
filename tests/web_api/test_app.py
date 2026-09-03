from collections.abc import Iterator
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from careloop.domain import Turn
from careloop.web_api.app import create_app
from careloop.web_api.contracts import (
    CreateSessionRequestV1,
    ParticipantSessionV1,
    PublicSessionStateV1,
    ReleaseDispositionV1,
    SseEventTypeV1,
    SseEventV1,
)
from careloop.web_api.identity import IdentityContextV1, IdentityRole
from careloop.web_api.reports import ParticipantSummaryV1, ResearchReportV1


class FakeService:
    def __init__(self) -> None:
        self.last_event_id: str | None = None
        self.calls: list[str] = []

    def create_session(
        self,
        request: CreateSessionRequestV1,
        *,
        idempotency_key: str,
        identity: IdentityContextV1,
    ) -> ParticipantSessionV1:
        self.calls.append(f"create:{idempotency_key}:{identity.role.value}")
        return _session()

    def submit_turn(self, *args: object, **kwargs: object) -> ParticipantSessionV1:
        self.calls.append("turn")
        return _session()

    def get_session(self, *args: object, **kwargs: object) -> ParticipantSessionV1:
        self.calls.append("session")
        return _session()

    def stream_events(
        self, *args: object, after_event_id: str | None, **kwargs: object
    ) -> Iterator[SseEventV1]:
        self.last_event_id = after_event_id
        yield SseEventV1(
            contract_version="v1",
            event_id="session-1:7",
            session_id="session-1",
            sequence=7,
            event_type=SseEventTypeV1.ANSWER_RELEASED,
            public_state=PublicSessionStateV1.ANSWER_AVAILABLE,
            release_disposition=ReleaseDispositionV1.ALLOW,
            released_turn=_turn(),
        )

    def decide_review(self, *args: object, **kwargs: object) -> ParticipantSessionV1:
        self.calls.append("review")
        return _session()

    def close_session(self, *args: object, **kwargs: object) -> ParticipantSessionV1:
        self.calls.append("close")
        return _session()

    def get_report(self, *args: object, **kwargs: object) -> ResearchReportV1:
        self.calls.append("report")
        return _report()

    def list_plugins(self, *args: object, **kwargs: object) -> dict[str, object]:
        self.calls.append("plugins")
        return {"contract_version": "v1", "plugins": []}

    def replace_plugin_profile(
        self, *args: object, **kwargs: object
    ) -> dict[str, object]:
        self.calls.append("profile")
        return {"contract_version": "v1", "profile_id": "profile-1"}

    def ready(self) -> bool:
        return True


def _identity(role: IdentityRole):
    def dependency() -> IdentityContextV1:
        return IdentityContextV1(
            contract_version="v1",
            subject=f"synthetic-local:{role.value}-1",
            role=role,
            auth_source="local_synthetic",
        )

    return dependency


def _turn() -> Turn:
    return Turn(
        turn_id="turn-1:assistant",
        sequence=1,
        role="assistant",
        text="Atomic released answer",
    )


def _session() -> ParticipantSessionV1:
    return ParticipantSessionV1(
        contract_version="v1",
        session_id="session-1",
        locale="en-US",
        public_state=PublicSessionStateV1.ANSWER_AVAILABLE,
        release_disposition=ReleaseDispositionV1.ALLOW,
        released_turns=(_turn(),),
    )


def _report() -> ResearchReportV1:
    return ResearchReportV1(
        contract_version="v1",
        report_id="report-1",
        session_id="session-1",
        created_at=datetime(2026, 9, 3, tzinfo=UTC),
        participant_summary=ParticipantSummaryV1(
            contract_version="v1",
            session_id="session-1",
            locale="en-US",
            title="Synthetic session summary",
            summary="The adult synthetic role-play session is closed.",
            released_turns=(_turn(),),
            disclosure="Not therapy, diagnosis, crisis care, or an emergency service.",
        ),
        evidence={"review_queue_is_simulated": True},
    )


def _client(role: IdentityRole) -> tuple[TestClient, FakeService]:
    service = FakeService()
    app = create_app(service=service, identity_dependency=_identity(role))
    return TestClient(app), service


def test_frozen_api_surface_and_operational_health_routes_exist() -> None:
    client, _ = _client(IdentityRole.ADMIN)
    paths = {route.path for route in client.app.routes}
    assert {
        "/api/v1/sessions",
        "/api/v1/sessions/{session_id}/turns",
        "/api/v1/sessions/{session_id}",
        "/api/v1/sessions/{session_id}/events",
        "/api/v1/reviews/{review_id}/decisions",
        "/api/v1/sessions/{session_id}/close",
        "/api/v1/sessions/{session_id}/report",
        "/api/v1/sessions/{session_id}/report.html",
        "/api/v1/sessions/{session_id}/report.pdf",
        "/api/v1/plugins",
        "/api/v1/plugin-profiles/{profile_id}",
        "/health/live",
        "/health/ready",
    } <= paths


def test_participant_create_requires_idempotency_and_synthetic_acknowledgement() -> (
    None
):
    client, service = _client(IdentityRole.PARTICIPANT)
    payload = {
        "contract_version": "v1",
        "session_id": "session-1",
        "scenario_id": "seed-support-en-v1",
        "locale": "en-US",
        "model_id": "deterministic-test-adapter",
        "policy_version": "v1",
        "plugin_profile_id": "profile-1",
        "evidence_registry_version": "v1",
        "adult_synthetic_role_play": True,
    }

    assert client.post("/api/v1/sessions", json=payload).status_code == 422
    response = client.post(
        "/api/v1/sessions",
        json=payload,
        headers={"Idempotency-Key": "create-1"},
    )
    assert response.status_code == 201
    assert response.json()["released_turns"] == [
        {
            "turn_id": "turn-1:assistant",
            "sequence": 1,
            "role": "assistant",
            "text": "Atomic released answer",
        }
    ]
    assert service.calls == ["create:create-1:participant"]


def test_sse_resumes_by_last_event_id_and_exposes_no_draft_fields() -> None:
    client, service = _client(IdentityRole.PARTICIPANT)
    response = client.get(
        "/api/v1/sessions/session-1/events",
        headers={"Last-Event-ID": "session-1:6"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert service.last_event_id == "session-1:6"
    assert "id: session-1:7" in response.text
    assert "Atomic released answer" in response.text
    prohibited = ("draft", "token", "gate", "exception", "secret", "reasoning")
    assert all(item not in response.text.casefold() for item in prohibited)


def test_role_separation_and_authorized_report_projection() -> None:
    participant, _ = _client(IdentityRole.PARTICIPANT)
    reviewer, _ = _client(IdentityRole.REVIEWER)
    admin, _ = _client(IdentityRole.ADMIN)

    decision = {
        "contract_version": "v1",
        "request_id": "review-request-1",
        "decision": "APPROVE",
        "expected_revision": 1,
        "resolved_at": "2026-09-03T00:00:00Z",
        "evidence_ids": ["review-evidence-1"],
        "replacement_turn": None,
    }
    assert (
        participant.post(
            "/api/v1/reviews/review-1/decisions",
            json=decision,
            headers={"Idempotency-Key": "review-request-1"},
        ).status_code
        == 403
    )
    assert reviewer.get("/api/v1/plugins").status_code == 403
    assert admin.get("/api/v1/plugins").status_code == 200

    participant_report = participant.get("/api/v1/sessions/session-1/report")
    assert participant_report.status_code == 200
    assert "evidence" not in participant_report.json()
    reviewer_report = reviewer.get("/api/v1/sessions/session-1/report")
    assert reviewer_report.status_code == 200
    assert reviewer_report.json()["evidence"] == {"review_queue_is_simulated": True}
    assert participant.get("/api/v1/sessions/session-1/report.html").status_code == 403
    assert reviewer.get("/api/v1/sessions/session-1/report.html").status_code == 200
    pdf = reviewer.get("/api/v1/sessions/session-1/report.pdf")
    assert pdf.status_code == 200
    assert pdf.content.startswith(b"%PDF-1.4")
