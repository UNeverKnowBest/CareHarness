"""Canonical research reports and deterministic passive reviewer renderings."""

import json
from html import escape
from typing import Self

from pydantic import AwareDatetime, JsonValue, model_validator

from careloop.agent_runtime.contracts import (
    ContractVersion,
    NonBlankStr,
    RuntimeContractModel,
)
from careloop.artifacts import canonical_json_bytes
from careloop.domain import Turn


class ParticipantSummaryV1(RuntimeContractModel):
    """Approved non-diagnostic summary without reviewer-only evidence."""

    contract_version: ContractVersion
    session_id: NonBlankStr
    locale: NonBlankStr
    title: NonBlankStr
    summary: NonBlankStr
    released_turns: tuple[Turn, ...]
    disclosure: NonBlankStr

    @model_validator(mode="after")
    def validate_released_turns(self) -> Self:
        if any(turn.role != "assistant" for turn in self.released_turns):
            raise ValueError(
                "participant summary contains released assistant turns only"
            )
        return self


class ResearchReportV1(RuntimeContractModel):
    """Versioned report source from which all audience renderings are derived."""

    contract_version: ContractVersion
    report_id: NonBlankStr
    session_id: NonBlankStr
    created_at: AwareDatetime
    participant_summary: ParticipantSummaryV1
    evidence: dict[str, JsonValue]

    @model_validator(mode="after")
    def validate_identity(self) -> Self:
        if self.participant_summary.session_id != self.session_id:
            raise ValueError("participant summary must match report session")
        return self


def canonical_report_json(report: ResearchReportV1) -> bytes:
    """Return the sole canonical JSON representation of a research report."""
    snapshot = ResearchReportV1.model_validate(report.model_dump())
    return canonical_json_bytes(snapshot)


def render_reviewer_html(report: ResearchReportV1) -> bytes:
    """Derive deterministic, escaped, script-free reviewer HTML."""
    snapshot = ResearchReportV1.model_validate(report.model_dump())
    summary = snapshot.participant_summary
    turns = "".join(
        "<li><strong>Released assistant turn</strong> "
        f"<code>{escape(turn.turn_id)}</code><p>{escape(turn.text)}</p></li>"
        for turn in summary.released_turns
    )
    evidence = escape(
        json.dumps(
            snapshot.evidence,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    document = f"""<!doctype html>
<html lang="{escape(summary.locale)}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CareLoop Research Review — {escape(snapshot.report_id)}</title>
<style>body{{font:16px/1.5 system-ui,sans-serif;max-width:900px;margin:auto;
padding:2rem;color:#172033}}.notice{{border:2px solid #8b5d12;padding:1rem;
background:#fff8e6}}code,pre{{overflow-wrap:anywhere}}li{{margin-block:1rem}}</style>
</head><body><main><p class="notice">Adult synthetic role-play research only.
The simulated review queue is not staffed care and contacts no clinician,
emergency service, family member, authority, or other third party.</p>
<h1>{escape(summary.title)}</h1><p>{escape(summary.summary)}</p>
<p>{escape(summary.disclosure)}</p><h2>Released content</h2><ol>{turns}</ol>
<h2>Reviewer evidence</h2><pre>{evidence}</pre>
</main></body></html>"""
    return document.encode("utf-8")


def render_reviewer_pdf(report: ResearchReportV1) -> bytes:
    """Derive a minimal deterministic passive PDF without links or actions."""
    snapshot = ResearchReportV1.model_validate(report.model_dump())
    lines = (
        "CareLoop Research Review",
        f"Report: {snapshot.report_id}",
        f"Session: {snapshot.session_id}",
        "Adult synthetic role-play research only.",
        "The simulated review queue is not staffed care or an emergency service.",
        "See the canonical JSON or passive HTML for complete Unicode evidence.",
    )
    commands = ["BT", "/F1 11 Tf", "50 790 Td"]
    for index, line in enumerate(lines):
        if index:
            commands.append("0 -18 Td")
        commands.append(f"({_pdf_text(line)}) Tj")
    commands.append("ET")
    stream = "\n".join(commands).encode("ascii")
    objects = (
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 842] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length "
        + str(len(stream)).encode("ascii")
        + b" >>\nstream\n"
        + stream
        + b"\nendstream",
    )
    output = bytearray(b"%PDF-1.4\n%CareLoop\n")
    offsets: list[int] = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{number} 0 obj\n".encode("ascii"))
        output.extend(body)
        output.extend(b"\nendobj\n")
    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF"
        ).encode("ascii")
    )
    return bytes(output)


def _pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
