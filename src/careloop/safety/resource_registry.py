"""Deterministic locale and explicit-as-of resource selection."""

from datetime import date
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from careloop.domain import CrisisResource
from careloop.safety.registry import SafetyPolicyModel, SafetyPolicySource


class ResourceSelectionStatus(StrEnum):
    SELECTED = "selected"
    MISSING_JURISDICTION = "missing_jurisdiction"
    JURISDICTION_MISMATCH = "jurisdiction_mismatch"
    OUTSIDE_AS_OF = "outside_as_of"
    LOADER_FAILURE = "loader_failure"


class ResourceSelection(SafetyPolicyModel):
    status: ResourceSelectionStatus
    resource: CrisisResource | None

    @model_validator(mode="after")
    def validate_status_resource_pair(self) -> Self:
        if (self.status is ResourceSelectionStatus.SELECTED) != (
            self.resource is not None
        ):
            raise ValueError("only a selected decision may contain a resource")
        return self


class ResourcePolicyRegistry(SafetyPolicyModel):
    policy_schema_version: Literal["v1"]
    resource_registry_version: Literal["v1"]
    sources: Annotated[tuple[SafetyPolicySource, ...], Field(min_length=1)]
    resources: Annotated[tuple[CrisisResource, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def validate_registry(self) -> Self:
        source_ids = tuple(source.source_id for source in self.sources)
        if len(set(source_ids)) != len(source_ids):
            raise ValueError("source_id values must be unique")
        source_urls = {source.locator for source in self.sources}

        resource_ids = tuple(resource.resource_id for resource in self.resources)
        if len(set(resource_ids)) != len(resource_ids):
            raise ValueError("resource_id values must be unique")
        jurisdictions = tuple(resource.jurisdiction for resource in self.resources)
        if len(set(jurisdictions)) != len(jurisdictions):
            raise ValueError("resource jurisdictions must be unique")

        for resource in self.resources:
            if resource.resource_registry_version != self.resource_registry_version:
                raise ValueError("resource_registry_version mismatch")
            if resource.source_url not in source_urls:
                raise ValueError(
                    f"resource source_url is not registered: {resource.source_url}"
                )
        return self

    def select(self, *, jurisdiction: str | None, as_of: date) -> ResourceSelection:
        if jurisdiction is None or not jurisdiction.strip():
            return ResourceSelection(
                status=ResourceSelectionStatus.MISSING_JURISDICTION,
                resource=None,
            )
        locale_matches = tuple(
            resource
            for resource in self.resources
            if resource.jurisdiction == jurisdiction
        )
        if not locale_matches:
            return ResourceSelection(
                status=ResourceSelectionStatus.JURISDICTION_MISMATCH,
                resource=None,
            )
        resource = locale_matches[0]
        if not (resource.verified_on <= as_of <= resource.expires_on):
            return ResourceSelection(
                status=ResourceSelectionStatus.OUTSIDE_AS_OF,
                resource=None,
            )
        return ResourceSelection(
            status=ResourceSelectionStatus.SELECTED,
            resource=resource,
        )


def load_resource_registry(path: str | Path) -> ResourcePolicyRegistry:
    return ResourcePolicyRegistry.model_validate_json(
        Path(path).read_text(encoding="utf-8")
    )
