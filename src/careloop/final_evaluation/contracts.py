"""Strict M17 corpus, isolated expectation, and evidence contracts."""

import json
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

from careloop.application.synthetic_turn import SyntheticTurnStatus
from careloop.artifacts import canonical_json_bytes


def _non_blank(value: str) -> str:
    if not value.strip():
        raise ValueError("must not be empty or whitespace")
    return value


NonBlank = Annotated[str, AfterValidator(_non_blank)]
Locale = Literal["en", "zh-CN"]
Variant = Literal["control", "challenge"]
ModelBehavior = Literal["scripted", "provider_failure"]


class FinalEvaluationModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class FinalEvaluationCaseV1(FinalEvaluationModel):
    case_id: NonBlank
    pair_id: NonBlank
    variant: Variant
    locale: Locale
    synthetic_only: Literal[True]
    input_text: NonBlank
    jurisdiction: NonBlank | None
    model_behavior: ModelBehavior
    draft_texts: tuple[NonBlank, ...] = Field(max_length=3)
    red_team_tags: tuple[NonBlank, ...]

    @model_validator(mode="after")
    def validate_stimulus(self) -> Self:
        if self.model_behavior == "provider_failure" and self.draft_texts:
            raise ValueError("provider_failure stimulus cannot contain draft text")
        if self.model_behavior == "scripted" and not self.draft_texts:
            raise ValueError("scripted stimulus requires at least one draft")
        if self.variant == "control" and self.red_team_tags:
            raise ValueError("control stimulus cannot carry red-team tags")
        if self.variant == "challenge" and not self.red_team_tags:
            raise ValueError("challenge stimulus requires red-team tags")
        if len(self.red_team_tags) != len(set(self.red_team_tags)):
            raise ValueError("red_team_tags must be unique")
        return self


class FinalEvaluationCorpusV1(FinalEvaluationModel):
    contract_version: Literal["v1"]
    corpus_id: NonBlank
    as_of: date
    cases: tuple[FinalEvaluationCaseV1, ...] = Field(min_length=16, max_length=16)

    @model_validator(mode="after")
    def validate_pairs(self) -> Self:
        case_ids = tuple(case.case_id for case in self.cases)
        if len(case_ids) != len(set(case_ids)):
            raise ValueError("case_id values must be unique")
        pairs: dict[str, list[FinalEvaluationCaseV1]] = defaultdict(list)
        for case in self.cases:
            pairs[case.pair_id].append(case)
        if len(pairs) != 8:
            raise ValueError("M17 corpus requires exactly eight matched pairs")
        for pair_id, cases in pairs.items():
            if tuple(case.variant for case in cases) != ("control", "challenge"):
                raise ValueError(
                    f"pair {pair_id!r} requires one control and one challenge in order"
                )
            if len({case.locale for case in cases}) != 1:
                raise ValueError(f"pair {pair_id!r} must use one locale")
        return self


class FinalEvaluationExpectationV1(FinalEvaluationModel):
    case_id: NonBlank
    expected_status: SyntheticTurnStatus
    expected_model_calls: int = Field(ge=0, le=3)
    expected_ordinary_release: bool
    expected_queue_entry: bool
    expected_normal_flow_suppressed: bool
    expected_resource_ids: tuple[NonBlank, ...]


class FinalEvaluationGoldV1(FinalEvaluationModel):
    gold_schema_version: Literal["v1"]
    corpus_id: NonBlank
    expectations: tuple[FinalEvaluationExpectationV1, ...] = Field(min_length=1)


class FinalEvaluationObservationV1(FinalEvaluationModel):
    case_id: NonBlank
    pair_id: NonBlank
    variant: Variant
    locale: Locale
    status: SyntheticTurnStatus
    model_calls: int = Field(ge=0)
    ordinary_release: bool
    queue_entry: bool
    normal_flow_suppressed: bool
    resource_ids: tuple[NonBlank, ...]
    runtime_event_types: tuple[NonBlank, ...] = Field(min_length=1)
    participant_projection_isolated: bool


class FinalEvaluationComparisonV1(FinalEvaluationModel):
    case_id: NonBlank
    status_matches: bool
    model_calls_match: bool
    ordinary_release_matches: bool
    queue_entry_matches: bool
    normal_flow_suppressed_matches: bool
    resource_ids_match: bool
    all_fields_match: bool

    @model_validator(mode="after")
    def validate_match_derivation(self) -> Self:
        expected = all(
            (
                self.status_matches,
                self.model_calls_match,
                self.ordinary_release_matches,
                self.queue_entry_matches,
                self.normal_flow_suppressed_matches,
                self.resource_ids_match,
            )
        )
        if self.all_fields_match != expected:
            raise ValueError("all_fields_match must derive from comparison fields")
        return self


class MatchedPairObservationV1(FinalEvaluationModel):
    pair_id: NonBlank
    control_case_id: NonBlank
    challenge_case_id: NonBlank
    contrast_observed: bool
    challenge_controlled: bool


class FinalEvaluationEvidenceV1(FinalEvaluationModel):
    evidence_schema_version: Literal["v1"]
    corpus_id: NonBlank
    as_of: date
    observations: tuple[FinalEvaluationObservationV1, ...] = Field(
        min_length=16, max_length=16
    )
    comparisons: tuple[FinalEvaluationComparisonV1, ...] = Field(
        min_length=16, max_length=16
    )
    matched_pairs: tuple[MatchedPairObservationV1, ...] = Field(
        min_length=8, max_length=8
    )
    limitations: tuple[NonBlank, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_evidence_order(self) -> Self:
        observation_ids = tuple(item.case_id for item in self.observations)
        comparison_ids = tuple(item.case_id for item in self.comparisons)
        if observation_ids != comparison_ids:
            raise ValueError("comparison order must match observation order")
        if len(observation_ids) != len(set(observation_ids)):
            raise ValueError("observation case IDs must be unique")
        pair_ids = tuple(item.pair_id for item in self.matched_pairs)
        if len(pair_ids) != len(set(pair_ids)):
            raise ValueError("matched pair IDs must be unique")
        return self

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self)


def load_final_evaluation_corpus(path: str | Path) -> FinalEvaluationCorpusV1:
    """Load local M17 stimuli without loading expectation data."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return FinalEvaluationCorpusV1.model_validate(payload)


def validate_final_evaluation_gold(
    gold: FinalEvaluationGoldV1, corpus: FinalEvaluationCorpusV1
) -> FinalEvaluationGoldV1:
    """Correlate expectation identities only at the comparison boundary."""
    if gold.corpus_id != corpus.corpus_id:
        raise ValueError("gold corpus_id must match evaluated corpus")
    gold_ids = tuple(item.case_id for item in gold.expectations)
    corpus_ids = tuple(item.case_id for item in corpus.cases)
    if gold_ids != corpus_ids:
        raise ValueError("gold case IDs must exactly match corpus case order")
    return FinalEvaluationGoldV1.model_validate(gold.model_dump())


def load_final_evaluation_gold(
    path: str | Path, corpus: FinalEvaluationCorpusV1
) -> FinalEvaluationGoldV1:
    """Load isolated M17 expectations after actual observations exist."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return validate_final_evaluation_gold(
        FinalEvaluationGoldV1.model_validate(payload), corpus
    )
