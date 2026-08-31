from pathlib import Path

from careloop.application import EvaluateTrajectory
from careloop.presentation import render_static_audit, write_static_audit

ROOT = Path(__file__).parents[2]
TRAJECTORY_ROOT = ROOT / "benchmarks" / "trajectories"
MANIFEST_PATH = ROOT / "benchmarks" / "manifest.v1.json"


def _service() -> EvaluateTrajectory:
    return EvaluateTrajectory.from_paths(
        benchmark_manifest_path=MANIFEST_PATH,
        process_policy_path=ROOT / "policies" / "process.v1.json",
        crisis_policy_path=ROOT / "policies" / "crisis.v1.json",
        resource_policy_path=ROOT / "policies" / "resources.v1.json",
        evaluation_policy_path=ROOT / "policies" / "evaluation.v1.json",
    )


def test_static_audit_renders_evidence_links_suppression_and_hash(
    tmp_path: Path,
) -> None:
    result = _service().run(TRAJECTORY_ROOT / "p7-good.json")
    output = tmp_path / "p7-good.html"

    first = write_static_audit(result, output)
    second = write_static_audit(result, output)

    assert first == second == output.read_bytes()
    assert b"\r" not in first
    html = output.read_text(encoding="utf-8")
    assert "CareLoop Evidence Audit" in html
    assert "Synthetic, frozen, non-clinical artifact evidence only" in html
    assert result.canonical_hash in html
    assert "NORMAL FLOW SUPPRESSED" in html
    assert 'id="turn-p7-t1"' in html
    assert 'href="#turn-p7-t1"' in html
    assert "Final-only evidence" in html
    assert "Trajectory-aware evidence" in html
    assert "score" not in html.casefold()
    assert "<script" not in html.casefold()
    assert "<link" not in html.casefold()
    assert "<img" not in html.casefold()


def test_static_audit_escapes_untrusted_trajectory_text() -> None:
    result = _service().run(TRAJECTORY_ROOT / "p1-good.json")
    hostile = result.model_copy(
        update={
            "trajectory": result.trajectory.model_copy(
                update={
                    "turns": (
                        result.trajectory.turns[0].model_copy(
                            update={"text": '<script>alert("synthetic")</script>'}
                        ),
                    )
                    + result.trajectory.turns[1:]
                }
            )
        }
    )

    html = render_static_audit(hostile).decode("utf-8")

    assert '<script>alert("synthetic")</script>' not in html
    assert "&lt;script&gt;alert(&quot;synthetic&quot;)&lt;/script&gt;" in html
    assert "<script" not in html.casefold()


def test_static_audit_shows_registered_resource_provenance() -> None:
    result = _service().run(TRAJECTORY_ROOT / "p8-good.json")

    html = render_static_audit(result).decode("utf-8")

    assert "synthetic-human-help-zz-test" in html
    assert "ZZ-TEST" in html
    assert "https://example.invalid/careloop/resources/zz-test-v1" in html
