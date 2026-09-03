"""Authoritative SQL projections used only by the removable M16 Web adapter."""

from datetime import date, datetime
from typing import Self

from pydantic import model_validator
from sqlalchemy import Connection, Engine, func, insert, select, update
from sqlalchemy.exc import IntegrityError

from careloop.agent_runtime.contracts import RuntimeContractModel
from careloop.domain import SafetyEvent, Turn
from careloop.durable_runtime.schema import public_session_events, research_sessions
from careloop.web_api.contracts import (
    CreateSessionRequestV1,
    ParticipantSessionV1,
    SseEventV1,
)
from careloop.web_api.reports import ResearchReportV1


class StoredResearchSessionV1(RuntimeContractModel):
    request: CreateSessionRequestV1
    participant: ParticipantSessionV1
    turns: tuple[Turn, ...]
    safety_events: tuple[SafetyEvent, ...]
    report: ResearchReportV1 | None
    owner_subject: str

    @model_validator(mode="after")
    def validate_session_identity(self) -> Self:
        if self.request.session_id != self.participant.session_id:
            raise ValueError("request and participant session must match")
        return self


class ResearchWebRepository:
    """Store participant projections, complete transcripts, reports, and SSE rows."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def create_session(
        self,
        *,
        request: CreateSessionRequestV1,
        participant: ParticipantSessionV1,
        owner_subject: str,
        created_at: datetime,
        retention_until: date,
        event: SseEventV1,
    ) -> None:
        try:
            with self._engine.begin() as connection:
                connection.execute(
                    insert(research_sessions).values(
                        session_id=request.session_id,
                        owner_subject=owner_subject,
                        scenario_id=request.scenario_id,
                        locale=request.locale,
                        created_at=created_at,
                        retention_until=retention_until,
                        request_payload=request.model_dump(mode="json"),
                        participant_payload=participant.model_dump(mode="json"),
                        transcript_payload={"turns": [], "safety_events": []},
                        report_payload=None,
                    )
                )
                self._insert_event(connection, event)
        except IntegrityError as error:
            raise ValueError("research session identity already exists") from error

    def load_session(self, session_id: str) -> StoredResearchSessionV1:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(
                        research_sessions.c.request_payload,
                        research_sessions.c.participant_payload,
                        research_sessions.c.transcript_payload,
                        research_sessions.c.report_payload,
                        research_sessions.c.owner_subject,
                    ).where(research_sessions.c.session_id == session_id)
                )
                .mappings()
                .first()
            )
        if row is None:
            raise KeyError(session_id)
        transcript = dict(row["transcript_payload"])
        report_payload = row["report_payload"]
        return StoredResearchSessionV1(
            request=CreateSessionRequestV1.model_validate(row["request_payload"]),
            participant=ParticipantSessionV1.model_validate(row["participant_payload"]),
            turns=tuple(Turn.model_validate(item) for item in transcript["turns"]),
            safety_events=tuple(
                SafetyEvent.model_validate(item) for item in transcript["safety_events"]
            ),
            report=(
                None
                if report_payload is None
                else ResearchReportV1.model_validate(report_payload)
            ),
            owner_subject=str(row["owner_subject"]),
        )

    def next_event_sequence(self, session_id: str) -> int:
        with self._engine.connect() as connection:
            maximum = connection.scalar(
                select(func.max(public_session_events.c.sequence)).where(
                    public_session_events.c.session_id == session_id
                )
            )
        return 0 if maximum is None else int(maximum) + 1

    def update_session(
        self,
        *,
        participant: ParticipantSessionV1,
        turns: tuple[Turn, ...],
        safety_events: tuple[SafetyEvent, ...],
        event: SseEventV1,
        report: ResearchReportV1 | None = None,
    ) -> None:
        with self._engine.begin() as connection:
            current = (
                connection.execute(
                    select(research_sessions.c.session_id)
                    .where(research_sessions.c.session_id == participant.session_id)
                    .with_for_update()
                )
                .mappings()
                .first()
            )
            if current is None:
                raise KeyError(participant.session_id)
            expected = connection.scalar(
                select(func.max(public_session_events.c.sequence)).where(
                    public_session_events.c.session_id == participant.session_id
                )
            )
            expected_sequence = 0 if expected is None else int(expected) + 1
            if event.sequence != expected_sequence:
                raise ValueError("public event sequence must be contiguous")
            changed = connection.execute(
                update(research_sessions)
                .where(research_sessions.c.session_id == participant.session_id)
                .values(
                    participant_payload=participant.model_dump(mode="json"),
                    transcript_payload={
                        "turns": [item.model_dump(mode="json") for item in turns],
                        "safety_events": [
                            item.model_dump(mode="json") for item in safety_events
                        ],
                    },
                    report_payload=(
                        None if report is None else report.model_dump(mode="json")
                    ),
                )
            )
            if changed.rowcount != 1:
                raise ValueError("research session update conflicted")
            self._insert_event(connection, event)

    def events_after(
        self, session_id: str, after_event_id: str | None
    ) -> tuple[SseEventV1, ...]:
        after_sequence = -1
        with self._engine.connect() as connection:
            if after_event_id is not None:
                found = connection.scalar(
                    select(public_session_events.c.sequence).where(
                        public_session_events.c.session_id == session_id,
                        public_session_events.c.event_id == after_event_id,
                    )
                )
                if found is None:
                    raise ValueError("Last-Event-ID is unknown for this session")
                after_sequence = int(found)
            rows = connection.execute(
                select(public_session_events.c.payload)
                .where(
                    public_session_events.c.session_id == session_id,
                    public_session_events.c.sequence > after_sequence,
                )
                .order_by(public_session_events.c.sequence)
            ).mappings()
            return tuple(SseEventV1.model_validate(row["payload"]) for row in rows)

    @staticmethod
    def _insert_event(connection: Connection, event: SseEventV1) -> None:
        connection.execute(
            insert(public_session_events).values(
                session_id=event.session_id,
                sequence=event.sequence,
                event_id=event.event_id,
                payload=event.model_dump(mode="json"),
            )
        )
