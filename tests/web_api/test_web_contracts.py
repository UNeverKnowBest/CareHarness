import pytest
from pydantic import ValidationError

from careloop.domain import Turn
from careloop.web_api.contracts import (
    ParticipantSessionV1,
    PublicSessionStateV1,
    ReleaseDispositionV1,
    SseEventTypeV1,
    SseEventV1,
)


def _released_turn() -> Turn:
    return Turn(
        turn_id="turn-1:assistant",
        sequence=1,
        role="assistant",
        text="A complete gated synthetic response.",
    )


def test_release_and_sse_vocabularies_are_exact() -> None:
    assert {item.value for item in ReleaseDispositionV1} == {
        "allow",
        "hold_for_review",
        "system_failure",
    }
    assert {item.value for item in SseEventTypeV1} == {
        "state_changed",
        "review_required",
        "answer_released",
        "session_closed",
        "failed_closed",
        "heartbeat",
    }


def test_answer_sse_contains_only_one_complete_released_turn() -> None:
    event = SseEventV1(
        contract_version="v1",
        event_id="session-1:7",
        session_id="session-1",
        sequence=7,
        event_type=SseEventTypeV1.ANSWER_RELEASED,
        public_state=PublicSessionStateV1.ANSWER_AVAILABLE,
        release_disposition=ReleaseDispositionV1.ALLOW,
        released_turn=_released_turn(),
    )

    assert set(event.model_dump()) == {
        "contract_version",
        "event_id",
        "session_id",
        "sequence",
        "event_type",
        "public_state",
        "release_disposition",
        "released_turn",
    }
    with pytest.raises(ValidationError):
        SseEventV1.model_validate({**event.model_dump(), "draft": "secret"})


@pytest.mark.parametrize(
    ("event_type", "state", "disposition"),
    [
        (
            SseEventTypeV1.REVIEW_REQUIRED,
            PublicSessionStateV1.REVIEW_PENDING,
            ReleaseDispositionV1.HOLD_FOR_REVIEW,
        ),
        (
            SseEventTypeV1.FAILED_CLOSED,
            PublicSessionStateV1.FAILED_CLOSED,
            ReleaseDispositionV1.SYSTEM_FAILURE,
        ),
    ],
)
def test_non_release_sse_rejects_an_ordinary_turn(
    event_type: SseEventTypeV1,
    state: PublicSessionStateV1,
    disposition: ReleaseDispositionV1,
) -> None:
    with pytest.raises(ValidationError):
        SseEventV1(
            contract_version="v1",
            event_id="session-1:8",
            session_id="session-1",
            sequence=8,
            event_type=event_type,
            public_state=state,
            release_disposition=disposition,
            released_turn=_released_turn(),
        )


def test_participant_session_retains_only_previously_released_assistant_turns() -> None:
    session = ParticipantSessionV1(
        contract_version="v1",
        session_id="session-1",
        locale="en-US",
        public_state=PublicSessionStateV1.REVIEW_PENDING,
        release_disposition=ReleaseDispositionV1.HOLD_FOR_REVIEW,
        released_turns=(_released_turn(),),
    )
    assert session.released_turns == (_released_turn(),)

    with pytest.raises(ValidationError):
        ParticipantSessionV1.model_validate(
            {
                **session.model_dump(),
                "released_turns": [
                    {
                        "turn_id": "turn-user",
                        "sequence": 0,
                        "role": "user",
                        "text": "must remain outside the participant answer projection",
                    }
                ],
            }
        )
