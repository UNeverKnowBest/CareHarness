from pathlib import Path

from careloop.final_evaluation import (
    FinalEvaluationEvidenceV1,
    load_final_evaluation_corpus,
    load_final_evaluation_gold,
    render_final_evaluation_markdown,
    run_final_evaluation,
)

ROOT = Path(__file__).parents[2]
CORPUS_PATH = ROOT / "benchmarks" / "final" / "m17.cases.v1.json"
GOLD_PATH = ROOT / "benchmarks" / "final" / "gold" / "m17.expectations.v1.json"
RAW_PATH = ROOT / "artifacts" / "raw" / "m17.final-evaluation.v1.json"
SUMMARY_PATH = ROOT / "artifacts" / "summary" / "m17.final-evaluation.v1.md"


def test_final_evaluation_runs_all_actual_cases_before_loading_gold() -> None:
    corpus = load_final_evaluation_corpus(CORPUS_PATH)
    trace: list[str] = []

    def gold_loader():
        trace.append("gold")
        return load_final_evaluation_gold(GOLD_PATH, corpus)

    evidence = run_final_evaluation(
        corpus,
        repository_root=ROOT,
        gold_loader=gold_loader,
        observation_sink=lambda case_id: trace.append(f"actual:{case_id}"),
    )

    assert trace[:-1] == [f"actual:{case.case_id}" for case in corpus.cases]
    assert trace[-1] == "gold"
    assert len(evidence.observations) == 16
    assert len(evidence.comparisons) == 16
    assert len(evidence.matched_pairs) == 8
    assert all(item.all_fields_match for item in evidence.comparisons)
    assert all(item.contrast_observed for item in evidence.matched_pairs)


def test_challenge_cases_release_no_ordinary_response_and_keep_runtime_evidence() -> (
    None
):
    corpus = load_final_evaluation_corpus(CORPUS_PATH)
    evidence = run_final_evaluation(
        corpus,
        repository_root=ROOT,
        gold_loader=lambda: load_final_evaluation_gold(GOLD_PATH, corpus),
    )
    variants = {case.case_id: case.variant for case in corpus.cases}
    challenges = tuple(
        item for item in evidence.observations if variants[item.case_id] == "challenge"
    )

    assert challenges
    assert all(not item.ordinary_release for item in challenges)
    assert all(item.runtime_event_types for item in challenges)
    assert all(item.participant_projection_isolated for item in challenges)
    assert any(item.normal_flow_suppressed for item in challenges)
    assert any(item.queue_entry for item in challenges)
    assert any(item.status == "failed_closed" for item in challenges)


def test_committed_m17_evidence_is_canonical_and_summary_is_derived() -> None:
    raw = RAW_PATH.read_bytes()
    evidence = FinalEvaluationEvidenceV1.model_validate_json(raw)
    assert evidence.canonical_bytes() == raw
    assert SUMMARY_PATH.read_bytes() == render_final_evaluation_markdown(evidence)
    markdown = SUMMARY_PATH.read_text(encoding="utf-8").casefold()
    for prohibited in (
        "clinical validity",
        "treatment effectiveness",
        "suicide detection accuracy",
        "aggregate score",
    ):
        assert f"claims {prohibited}" not in markdown
    assert "descriptive regression evidence only" in markdown


def test_final_evaluation_is_removable_and_has_no_network_or_wall_clock_input() -> None:
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(
            (ROOT / "src" / "careloop" / "final_evaluation").glob("*.py")
        )
    ).casefold()
    assert "datetime.now" not in source
    assert "httpx" not in source
    assert "requests" not in source

    inner_roots = (
        "domain",
        "process",
        "safety",
        "evaluation",
        "artifacts",
        "reporting",
        "agent_runtime",
    )
    for root in inner_roots:
        for path in (ROOT / "src" / "careloop" / root).rglob("*.py"):
            assert "careloop.final_evaluation" not in path.read_text(encoding="utf-8")
