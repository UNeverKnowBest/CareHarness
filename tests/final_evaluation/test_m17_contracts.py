import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from careloop.final_evaluation import (
    FinalEvaluationCorpusV1,
    FinalEvaluationGoldV1,
    load_final_evaluation_corpus,
    load_final_evaluation_gold,
    validate_final_evaluation_gold,
)

ROOT = Path(__file__).parents[2]
CORPUS_PATH = ROOT / "benchmarks" / "final" / "m17.cases.v1.json"
GOLD_PATH = ROOT / "benchmarks" / "final" / "gold" / "m17.expectations.v1.json"


def test_m17_corpus_and_gold_are_strict_separate_and_bilingual() -> None:
    corpus = load_final_evaluation_corpus(CORPUS_PATH)
    gold = load_final_evaluation_gold(GOLD_PATH, corpus)

    assert corpus.contract_version == "v1"
    assert corpus.corpus_id == "m17-final-evaluation-v1"
    assert corpus.as_of.isoformat() == "2026-09-04"
    assert len(corpus.cases) == 16
    assert len(gold.expectations) == 16
    assert {case.locale for case in corpus.cases} == {"en", "zh-CN"}
    assert {case.variant for case in corpus.cases} == {"control", "challenge"}
    assert len({case.pair_id for case in corpus.cases}) == 8
    assert all(case.synthetic_only for case in corpus.cases)

    case_payload = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    gold_payload = json.loads(GOLD_PATH.read_text(encoding="utf-8"))
    assert "expected_status" not in CORPUS_PATH.read_text(encoding="utf-8")
    assert "input_text" not in GOLD_PATH.read_text(encoding="utf-8")
    assert set(case_payload) == {"contract_version", "corpus_id", "as_of", "cases"}
    assert set(gold_payload) == {
        "gold_schema_version",
        "corpus_id",
        "expectations",
    }


def test_m17_contracts_reject_unknown_fields_duplicate_pairs_and_misaligned_gold() -> (
    None
):
    corpus = load_final_evaluation_corpus(CORPUS_PATH)
    payload = corpus.model_dump(mode="json")
    payload["unexpected"] = True
    with pytest.raises(ValidationError):
        FinalEvaluationCorpusV1.model_validate(payload)

    payload = corpus.model_dump(mode="json")
    payload["cases"][1]["variant"] = "control"
    payload["cases"][1]["red_team_tags"] = []
    with pytest.raises(ValidationError, match="control and one challenge"):
        FinalEvaluationCorpusV1.model_validate(payload)

    gold = load_final_evaluation_gold(GOLD_PATH, corpus)
    gold_payload = gold.model_dump(mode="json")
    gold_payload["expectations"] = gold_payload["expectations"][:-1]
    with pytest.raises(ValueError, match="exactly match corpus case order"):
        validate_final_evaluation_gold(
            FinalEvaluationGoldV1.model_validate(gold_payload), corpus
        )
