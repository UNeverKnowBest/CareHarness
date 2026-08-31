"""Deterministic, escaped, no-script HTML rendering for audit evidence."""

from html import escape
from pathlib import Path

from careloop.domain import Finding
from careloop.evaluation import TrajectoryEvaluationResult


def _finding_rows(findings: tuple[Finding, ...]) -> str:
    rows: list[str] = []
    for finding in findings:
        turn_links = " ".join(
            f'<a class="turn-link" href="#turn-{escape(turn_id)}">{escape(turn_id)}</a>'
            for turn_id in finding.turn_ids
        )
        sources = " ".join(
            f'<span class="source">{escape(source_id)}</span>'
            for source_id in finding.source_ids
        )
        rows.append(
            "<tr>"
            f"<td><code>{escape(finding.rule_id)}</code></td>"
            f'<td><span class="outcome {escape(finding.outcome)}">'
            f"{escape(finding.outcome)}</span></td>"
            f"<td>{turn_links}</td>"
            f"<td>{sources}</td>"
            "</tr>"
        )
    return "".join(rows)


def _ledger(title: str, findings: tuple[Finding, ...]) -> str:
    return (
        '<section class="ledger">'
        f"<h2>{escape(title)}</h2>"
        '<div class="table-wrap"><table><thead><tr>'
        "<th>Rule</th><th>Outcome</th><th>Evidence turns</th><th>Sources</th>"
        "</tr></thead><tbody>"
        f"{_finding_rows(findings)}"
        "</tbody></table></div></section>"
    )


def _timeline(result: TrajectoryEvaluationResult) -> str:
    marker_by_turn: dict[str, list[str]] = {}
    for marker in result.trajectory.process_markers:
        marker_by_turn.setdefault(marker.turn_id, []).append(
            f"{escape(marker.marker_type)}={escape(marker.value)}"
        )
    event_by_turn: dict[str, list[str]] = {}
    for event in result.trajectory.safety_events:
        suppression = (
            "NORMAL FLOW SUPPRESSED" if event.normal_flow_suppressed else "normal flow"
        )
        detail = (
            f"{escape(event.action.value)} · {escape(suppression)} · "
            f"event {escape(event.event_id)}"
        )
        for turn_id in event.triggering_turn_ids:
            event_by_turn.setdefault(turn_id, []).append(detail)
    cards: list[str] = []
    for turn in result.trajectory.turns:
        markers = "".join(
            f'<span class="marker">{value}</span>'
            for value in marker_by_turn.get(turn.turn_id, [])
        )
        events = "".join(
            f'<div class="event">{value}</div>'
            for value in event_by_turn.get(turn.turn_id, [])
        )
        cards.append(
            f'<article class="turn {escape(turn.role)}" '
            f'id="turn-{escape(turn.turn_id)}">'
            '<div class="turn-meta">'
            f"<span>{escape(turn.role)}</span>"
            f"<code>{escape(turn.turn_id)}</code>"
            f"<span>sequence {turn.sequence}</span>"
            "</div>"
            f"<p>{escape(turn.text)}</p>"
            f'<div class="markers">{markers}</div>{events}'
            "</article>"
        )
    return "".join(cards)


def _resources(result: TrajectoryEvaluationResult) -> str:
    if not result.resource_references:
        return '<p class="muted">No resource reference recorded.</p>'
    cards: list[str] = []
    for evidence in result.resource_references:
        if evidence.resource is None:
            cards.append(
                '<article class="resource unregistered">'
                f"<h3>{escape(evidence.resource_id)}</h3>"
                "<p>Unregistered resource reference.</p></article>"
            )
            continue
        resource = evidence.resource
        cards.append(
            '<article class="resource">'
            f"<h3>{escape(resource.resource_id)}</h3>"
            f"<p>{escape(resource.name)}</p>"
            "<dl><dt>Jurisdiction</dt>"
            f"<dd>{escape(resource.jurisdiction)}</dd>"
            "<dt>Registry version</dt>"
            f"<dd>{escape(resource.resource_registry_version)}</dd>"
            "<dt>Active dates</dt>"
            f"<dd>{resource.verified_on.isoformat()} — "
            f"{resource.expires_on.isoformat()}</dd>"
            "<dt>Provenance</dt>"
            f"<dd><code>{escape(resource.source_url)}</code></dd></dl>"
            "</article>"
        )
    return "".join(cards)


def render_static_audit(result: TrajectoryEvaluationResult) -> bytes:
    """Render one application result without scripts, external assets, or I/O."""
    suppression = any(
        event.normal_flow_suppressed for event in result.trajectory.safety_events
    )
    suppression_banner = (
        '<div class="suppression">NORMAL FLOW SUPPRESSED</div>' if suppression else ""
    )
    document = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CareLoop Evidence Audit — {escape(result.case_id)}</title>
<style>
:root{{--ink:#172033;--muted:#64748b;--paper:#f7f8fb;--card:#fff;--line:#dce2ea;
--present:#a51d37;--absent:#17724d;--uncertain:#8b5d12;--accent:#3f5fce}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);
font:15px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}}
main{{max-width:1420px;margin:auto;padding:32px}}
header{{display:grid;gap:12px;margin-bottom:28px}}
h1,h2,h3,p{{margin-top:0}}
h1{{font-size:clamp(28px,4vw,48px);letter-spacing:-.035em}}
.boundary{{padding:10px 14px;border:1px solid #efc26b;background:#fff8e6;
border-radius:10px}}
.meta{{display:flex;flex-wrap:wrap;gap:8px}}
.meta span,.marker,.source{{border:1px solid var(--line);border-radius:999px;
padding:4px 9px;background:var(--card)}}
code{{font-size:.86em}}
.suppression{{padding:13px 16px;border-radius:10px;background:#2b1630;color:#fff;
font-weight:800;letter-spacing:.08em}}
.layout{{display:grid;grid-template-columns:minmax(300px,.78fr) minmax(0,1.5fr);
gap:24px;align-items:start}}
section{{margin-bottom:26px}}.timeline{{position:sticky;top:18px}}
.turn,.ledger,.resource{{background:var(--card);border:1px solid var(--line);
border-radius:14px;padding:16px;margin-bottom:12px;box-shadow:0 8px 24px #1720330a}}
.turn.assistant{{border-left:5px solid var(--accent)}}
.turn.user{{border-left:5px solid #7c8aa5}}
.turn-meta{{display:flex;flex-wrap:wrap;gap:9px;color:var(--muted);font-size:.82rem;
text-transform:uppercase}}
.turn p{{white-space:pre-wrap;margin:12px 0}}
.markers{{display:flex;flex-wrap:wrap;gap:6px}}
.event{{margin-top:10px;padding:9px;border-radius:8px;background:#f4eafa;
font-weight:700}}
.ledgers{{display:grid;gap:18px}}.table-wrap{{overflow-x:auto}}
table{{width:100%;border-collapse:collapse}}
th,td{{padding:10px;text-align:left;vertical-align:top;
border-bottom:1px solid var(--line)}}
th{{color:var(--muted);font-size:.78rem;text-transform:uppercase}}
.outcome{{display:inline-block;border-radius:999px;padding:3px 8px;font-weight:750}}
.outcome.present{{color:var(--present);background:#fdebf0}}
.outcome.absent{{color:var(--absent);background:#e7f6ef}}
.outcome.uncertain{{color:var(--uncertain);background:#fff3dc}}
.turn-link{{display:inline-block;margin:0 5px 5px 0;color:var(--accent)}}
.source{{display:inline-block;margin:0 5px 5px 0;font-size:.78rem}}
dl{{display:grid;grid-template-columns:max-content 1fr;gap:6px 12px}}
dt{{color:var(--muted)}}dd{{margin:0;overflow-wrap:anywhere}}
.muted{{color:var(--muted)}}
@media(max-width:900px){{
main{{padding:18px}}.layout{{grid-template-columns:1fr}}.timeline{{position:static}}
}}
</style>
</head>
<body><main>
<header>
<p class="boundary">Synthetic, frozen, non-clinical artifact evidence only.</p>
<h1>CareLoop Evidence Audit</h1>
<div class="meta"><span>Case <strong>{escape(result.case_id)}</strong></span>
<span>as_of {result.as_of.isoformat()}</span>
<span>evaluator {escape(result.evaluation_manifest.evaluator_version)}</span></div>
<code>{escape(result.canonical_hash)}</code>{suppression_banner}
</header>
<div class="layout">
<section class="timeline"><h2>Trajectory timeline</h2>{_timeline(result)}</section>
<div>
<div class="ledgers">
{_ledger("Final-only evidence", result.final_answer_findings)}
{_ledger("Trajectory-aware evidence", result.trajectory_findings)}
</div>
<section><h2>Resource provenance</h2>{_resources(result)}</section>
</div>
</div>
</main></body></html>"""
    return document.encode("utf-8")


def write_static_audit(result: TrajectoryEvaluationResult, path: str | Path) -> bytes:
    """Write deterministic audit bytes and return the exact stored content."""
    content = render_static_audit(result)
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)
    return content
