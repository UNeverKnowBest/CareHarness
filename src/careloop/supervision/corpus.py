"""Strict loader for the fixed M15 bilingual synthetic supervision corpus."""

import json
from pathlib import Path
from typing import Literal, Self

from pydantic import Field, model_validator

from careloop.agent_runtime import DraftDecision
from careloop.agent_runtime.contracts import (
    ContractVersion,
    NonBlankStr,
    RuntimeContractModel,
)
from careloop.application.synthetic_turn import SyntheticTurnStatus

SupervisionCaseKind = Literal[
    "safe_allow",
    "input_override",
    "repair_allow",
    "repair_exhausted",
]
SupervisionLocale = Literal["en", "zh-CN"]


class SupervisionCaseV1(RuntimeContractModel):
    case_id: NonBlankStr
    locale: SupervisionLocale
    case_kind: SupervisionCaseKind
    synthetic_only: Literal[True]
    input_text: NonBlankStr
    draft_texts: tuple[NonBlankStr, ...]
    gate_decisions: tuple[DraftDecision, ...]
    expected_status: SyntheticTurnStatus
    expected_model_calls: int = Field(ge=0, le=3)
    expected_ordinary_release: bool
    expected_queue_entry: bool

    @model_validator(mode="after")
    def validate_expected_observations(self) -> Self:
        if len(self.draft_texts) != self.expected_model_calls:
            raise ValueError("draft_texts must match expected_model_calls")
        if len(self.gate_decisions) != self.expected_model_calls:
            raise ValueError("gate_decisions must match expected_model_calls")
        if self.expected_ordinary_release != (
            self.expected_status is SyntheticTurnStatus.RELEASED
        ):
            raise ValueError("ordinary release must match released status")
        if self.expected_queue_entry != (
            self.expected_status is SyntheticTurnStatus.AWAITING_HUMAN_REVIEW
        ):
            raise ValueError("queue entry must match review-hold status")
        return self


class SupervisionCorpusV1(RuntimeContractModel):
    contract_version: ContractVersion
    corpus_id: NonBlankStr
    cases: tuple[SupervisionCaseV1, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_cases(self) -> Self:
        case_ids = tuple(case.case_id for case in self.cases)
        if len(case_ids) != len(set(case_ids)):
            raise ValueError("case_id values must be unique")
        return self


def load_supervision_corpus(path: Path) -> SupervisionCorpusV1:
    """Load local versioned synthetic cases; no gold or network input is used."""
    return SupervisionCorpusV1.model_validate(json.loads(path.read_text("utf-8")))
