from datetime import UTC, datetime

from careloop.domain import Turn
from careloop.web_api.reports import (
    ParticipantSummaryV1,
    ResearchReportV1,
    canonical_report_json,
    render_reviewer_html,
    render_reviewer_pdf,
)


def _report() -> ResearchReportV1:
    summary = ParticipantSummaryV1(
        contract_version="v1",
        session_id="session-1",
        locale="zh-CN",
        title="研究演示摘要",
        summary="本次合成角色扮演已结束。<script>alert(1)</script>",
        released_turns=(
            Turn(
                turn_id="turn-1:assistant",
                sequence=1,
                role="assistant",
                text="合成回答",
            ),
        ),
        disclosure=("仅限成人合成角色扮演研究；不是治疗、诊断、危机照护或紧急服务。"),
    )
    return ResearchReportV1(
        contract_version="v1",
        report_id="report-1",
        session_id="session-1",
        created_at=datetime(2026, 9, 3, 12, tzinfo=UTC),
        participant_summary=summary,
        evidence={
            "artifact_hash": "sha256:" + "a" * 64,
            "review_queue_is_simulated": True,
        },
    )


def test_research_report_json_is_canonical_and_deterministic() -> None:
    first = canonical_report_json(_report())
    second = canonical_report_json(_report())

    assert first == second
    assert first.startswith(b'{"contract_version":"v1"')
    assert not first.endswith(b"\n")
    assert "研究演示摘要".encode() in first


def test_reviewer_html_escapes_content_and_has_no_active_or_remote_assets() -> None:
    rendered = render_reviewer_html(_report()).decode()

    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in rendered
    assert "<script" not in rendered.casefold()
    assert "http://" not in rendered.casefold()
    assert "https://" not in rendered.casefold()
    assert "simulated" in rendered.casefold()
    assert "not staffed care" in rendered.casefold()


def test_reviewer_pdf_is_deterministic_and_contains_no_active_content() -> None:
    first = render_reviewer_pdf(_report())
    second = render_reviewer_pdf(_report())

    assert first == second
    assert first.startswith(b"%PDF-1.4")
    assert b"/JavaScript" not in first
    assert b"/OpenAction" not in first
    assert b"CareLoop Research Review" in first
