"""Immutable raw evaluation result models for application and presentation."""

import json
from datetime import date
from typing import Annotated, Literal, Self

from pydantic import AfterValidator, BaseModel, ConfigDict, model_validator

from careloop.domain import (
    CrisisResource,
    EvaluationManifest,
    FinalAnswerView,
    Finding,
    Trajectory,
)


def _non_blank(value: str) -> str:
    if not value.strip():
        raise ValueError("must not be empty or whitespace")
    return value


NonBlank = Annotated[str, AfterValidator(_non_blank)]


class EvaluationResultModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ResourceReferenceEvidence(EvaluationResultModel):
    resource_id: NonBlank
    registered: bool
    resource: CrisisResource | None

    @model_validator(mode="after")
    def validate_reference(self) -> Self:
        if self.registered != (self.resource is not None):
            raise ValueError("registered must reflect whether resource metadata exists")
        if self.resource is not None and self.resource.resource_id != self.resource_id:
            raise ValueError("resource metadata identity must match resource_id")
        return self


class TrajectoryEvaluationResult(EvaluationResultModel):
    result_schema_version: Literal["v1"]
    case_id: NonBlank
    canonical_hash: NonBlank
    evaluation_manifest: EvaluationManifest
    as_of: date
    trajectory: Trajectory
    final_answer: FinalAnswerView
    final_answer_findings: tuple[Finding, ...]
    trajectory_findings: tuple[Finding, ...]
    resource_references: tuple[ResourceReferenceEvidence, ...]

    def canonical_bytes(self) -> bytes:
        """Return deterministic raw result bytes without runtime metadata."""
        return json.dumps(
            self.model_dump(mode="json"),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
