"""Removable M17 final evaluation package."""

from careloop.final_evaluation.contracts import (
    FinalEvaluationCaseV1,
    FinalEvaluationComparisonV1,
    FinalEvaluationCorpusV1,
    FinalEvaluationEvidenceV1,
    FinalEvaluationExpectationV1,
    FinalEvaluationGoldV1,
    FinalEvaluationObservationV1,
    MatchedPairObservationV1,
    load_final_evaluation_corpus,
    load_final_evaluation_gold,
    validate_final_evaluation_gold,
)
from careloop.final_evaluation.runner import (
    render_final_evaluation_markdown,
    run_final_evaluation,
)

__all__ = [
    "FinalEvaluationCaseV1",
    "FinalEvaluationComparisonV1",
    "FinalEvaluationCorpusV1",
    "FinalEvaluationEvidenceV1",
    "FinalEvaluationExpectationV1",
    "FinalEvaluationGoldV1",
    "FinalEvaluationObservationV1",
    "MatchedPairObservationV1",
    "load_final_evaluation_corpus",
    "load_final_evaluation_gold",
    "render_final_evaluation_markdown",
    "run_final_evaluation",
    "validate_final_evaluation_gold",
]
