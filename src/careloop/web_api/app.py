"""FastAPI adapter over injected M16 research application services."""

from collections.abc import Callable, Iterable
from typing import Protocol

from fastapi import Depends, FastAPI, Header, Request, Response, status
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import JsonValue

from careloop.artifacts import canonical_json_bytes
from careloop.web_api.contracts import (
    CloseSessionRequestV1,
    CreateSessionRequestV1,
    HealthViewV1,
    ParticipantSessionV1,
    PluginProfileUpdateRequestV1,
    ReviewDecisionRequestV1,
    SseEventV1,
    SubmitTurnRequestV1,
)
from careloop.web_api.identity import IdentityContextV1, IdentityRole, require_role
from careloop.web_api.reports import (
    ResearchReportV1,
    canonical_report_json,
    render_reviewer_html,
    render_reviewer_pdf,
)


class ResearchApiService(Protocol):
    """Application-service facade; HTTP never reaches storage or policy directly."""

    def create_session(
        self,
        request: CreateSessionRequestV1,
        *,
        idempotency_key: str,
        identity: IdentityContextV1,
    ) -> ParticipantSessionV1: ...

    def submit_turn(
        self,
        session_id: str,
        request: SubmitTurnRequestV1,
        *,
        idempotency_key: str,
        identity: IdentityContextV1,
    ) -> ParticipantSessionV1: ...

    def get_session(
        self, session_id: str, *, identity: IdentityContextV1
    ) -> ParticipantSessionV1: ...

    def stream_events(
        self,
        session_id: str,
        *,
        after_event_id: str | None,
        identity: IdentityContextV1,
    ) -> Iterable[SseEventV1]: ...

    def decide_review(
        self,
        review_id: str,
        request: ReviewDecisionRequestV1,
        *,
        idempotency_key: str,
        identity: IdentityContextV1,
    ) -> ParticipantSessionV1: ...

    def close_session(
        self,
        session_id: str,
        request: CloseSessionRequestV1,
        *,
        idempotency_key: str,
        identity: IdentityContextV1,
    ) -> ParticipantSessionV1: ...

    def get_report(
        self, session_id: str, *, identity: IdentityContextV1
    ) -> ResearchReportV1: ...

    def list_plugins(self, *, identity: IdentityContextV1) -> dict[str, JsonValue]: ...

    def replace_plugin_profile(
        self,
        profile_id: str,
        request: PluginProfileUpdateRequestV1,
        *,
        idempotency_key: str,
        identity: IdentityContextV1,
    ) -> dict[str, JsonValue]: ...

    def ready(self) -> bool: ...


IdentityDependency = Callable[..., IdentityContextV1]


def create_app(
    *,
    service: ResearchApiService,
    identity_dependency: IdentityDependency,
) -> FastAPI:
    """Build a removable API whose only business dependency is a service facade."""
    app = FastAPI(
        title="CareLoop adult synthetic role-play research API",
        version="v1",
        docs_url=None,
        redoc_url=None,
    )

    @app.exception_handler(PermissionError)
    async def permission_error(
        _request: Request, _error: PermissionError
    ) -> JSONResponse:
        return JSONResponse(status_code=403, content={"detail": "forbidden"})

    @app.exception_handler(KeyError)
    async def missing_error(_request: Request, _error: KeyError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": "not found"})

    @app.exception_handler(ValueError)
    async def conflict_error(_request: Request, _error: ValueError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": "request conflict"})

    def identity(
        value: IdentityContextV1 = Depends(identity_dependency),
    ) -> IdentityContextV1:
        return value

    @app.post(
        "/api/v1/sessions",
        response_model=ParticipantSessionV1,
        status_code=status.HTTP_201_CREATED,
    )
    def create_session(
        request: CreateSessionRequestV1,
        idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
        actor: IdentityContextV1 = Depends(identity),
    ) -> ParticipantSessionV1:
        require_role(actor, IdentityRole.PARTICIPANT)
        return service.create_session(
            request,
            idempotency_key=idempotency_key,
            identity=actor,
        )

    @app.post(
        "/api/v1/sessions/{session_id}/turns",
        response_model=ParticipantSessionV1,
    )
    def submit_turn(
        session_id: str,
        request: SubmitTurnRequestV1,
        idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
        actor: IdentityContextV1 = Depends(identity),
    ) -> ParticipantSessionV1:
        require_role(actor, IdentityRole.PARTICIPANT)
        return service.submit_turn(
            session_id,
            request,
            idempotency_key=idempotency_key,
            identity=actor,
        )

    @app.get(
        "/api/v1/sessions/{session_id}",
        response_model=ParticipantSessionV1,
    )
    def get_session(
        session_id: str,
        actor: IdentityContextV1 = Depends(identity),
    ) -> ParticipantSessionV1:
        require_role(actor, IdentityRole.PARTICIPANT)
        return service.get_session(session_id, identity=actor)

    @app.get("/api/v1/sessions/{session_id}/events")
    def session_events(
        session_id: str,
        last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
        actor: IdentityContextV1 = Depends(identity),
    ) -> StreamingResponse:
        require_role(actor, IdentityRole.PARTICIPANT)
        events = service.stream_events(
            session_id,
            after_event_id=last_event_id,
            identity=actor,
        )
        return StreamingResponse(
            _sse_chunks(events),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-transform",
                "X-Accel-Buffering": "no",
            },
        )

    @app.post(
        "/api/v1/reviews/{review_id}/decisions",
        response_model=ParticipantSessionV1,
    )
    def decide_review(
        review_id: str,
        request: ReviewDecisionRequestV1,
        idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
        actor: IdentityContextV1 = Depends(identity),
    ) -> ParticipantSessionV1:
        require_role(actor, IdentityRole.REVIEWER)
        return service.decide_review(
            review_id,
            request,
            idempotency_key=idempotency_key,
            identity=actor,
        )

    @app.post(
        "/api/v1/sessions/{session_id}/close",
        response_model=ParticipantSessionV1,
    )
    def close_session(
        session_id: str,
        request: CloseSessionRequestV1,
        idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
        actor: IdentityContextV1 = Depends(identity),
    ) -> ParticipantSessionV1:
        require_role(actor, IdentityRole.PARTICIPANT)
        return service.close_session(
            session_id,
            request,
            idempotency_key=idempotency_key,
            identity=actor,
        )

    @app.get("/api/v1/sessions/{session_id}/report")
    def report_json(
        session_id: str,
        actor: IdentityContextV1 = Depends(identity),
    ) -> Response:
        require_role(
            actor,
            IdentityRole.PARTICIPANT,
            IdentityRole.REVIEWER,
            IdentityRole.ADMIN,
        )
        report = service.get_report(session_id, identity=actor)
        content = (
            canonical_json_bytes(report.participant_summary)
            if actor.role is IdentityRole.PARTICIPANT
            else canonical_report_json(report)
        )
        return Response(content=content, media_type="application/json")

    @app.get("/api/v1/sessions/{session_id}/report.html")
    def report_html(
        session_id: str,
        actor: IdentityContextV1 = Depends(identity),
    ) -> Response:
        require_role(actor, IdentityRole.REVIEWER, IdentityRole.ADMIN)
        report = service.get_report(session_id, identity=actor)
        return Response(content=render_reviewer_html(report), media_type="text/html")

    @app.get("/api/v1/sessions/{session_id}/report.pdf")
    def report_pdf(
        session_id: str,
        actor: IdentityContextV1 = Depends(identity),
    ) -> Response:
        require_role(actor, IdentityRole.REVIEWER, IdentityRole.ADMIN)
        report = service.get_report(session_id, identity=actor)
        return Response(
            content=render_reviewer_pdf(report), media_type="application/pdf"
        )

    @app.get("/api/v1/plugins")
    def list_plugins(
        actor: IdentityContextV1 = Depends(identity),
    ) -> dict[str, JsonValue]:
        require_role(actor, IdentityRole.ADMIN)
        return service.list_plugins(identity=actor)

    @app.put("/api/v1/plugin-profiles/{profile_id}")
    def replace_plugin_profile(
        profile_id: str,
        request: PluginProfileUpdateRequestV1,
        idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
        actor: IdentityContextV1 = Depends(identity),
    ) -> dict[str, JsonValue]:
        require_role(actor, IdentityRole.ADMIN)
        return service.replace_plugin_profile(
            profile_id,
            request,
            idempotency_key=idempotency_key,
            identity=actor,
        )

    @app.get("/health/live", response_model=HealthViewV1)
    def live() -> HealthViewV1:
        return HealthViewV1(contract_version="v1", status="ok")

    @app.get("/health/ready", response_model=HealthViewV1)
    def ready() -> HealthViewV1:
        if not service.ready():
            raise HTTPException(status_code=503, detail="not ready")
        return HealthViewV1(contract_version="v1", status="ok")

    return app


def _sse_chunks(events: Iterable[SseEventV1]) -> Iterable[bytes]:
    for event in events:
        snapshot = SseEventV1.model_validate(event.model_dump())
        data = canonical_json_bytes(snapshot).decode("utf-8")
        yield (
            f"id: {snapshot.event_id}\n"
            f"event: {snapshot.event_type.value}\n"
            f"data: {data}\n\n"
        ).encode()
