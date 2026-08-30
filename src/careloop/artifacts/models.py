"""Internal frozen-artifact envelope without changing public domain schemas."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from careloop.artifacts.canonical import (
    HASH_EXCLUDED_FIELDS,
    canonical_json_bytes,
    canonical_sha256,
)
from careloop.domain import Trajectory


class ArtifactModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RuntimeMetadata(ArtifactModel):
    """Optional non-semantic timing evidence excluded from artifact hashes."""

    duration_ms: Annotated[int, Field(ge=0)]


class FrozenTrajectoryArtifact(ArtifactModel):
    """One validated trajectory and its deterministic content hash."""

    artifact_schema_version: Literal["v1"]
    canonical_hash: Annotated[str, Field(pattern=r"^sha256:[0-9a-f]{64}$")]
    case_id: Annotated[str, Field(min_length=1)]
    runtime_metadata: RuntimeMetadata | None
    trajectory: Trajectory

    def canonical_payload_bytes(self) -> bytes:
        """Return the exact bytes covered by ``canonical_hash``."""
        return canonical_json_bytes(self, exclude_fields=HASH_EXCLUDED_FIELDS)

    def stored_bytes(self) -> bytes:
        """Return the complete envelope in canonical UTF-8 JSON."""
        return canonical_json_bytes(self)


def build_frozen_trajectory_artifact(
    *,
    case_id: str,
    trajectory: Trajectory,
    runtime_metadata: RuntimeMetadata | None = None,
) -> FrozenTrajectoryArtifact:
    """Build the same envelope and hash for the same validated inputs."""
    payload = {
        "artifact_schema_version": "v1",
        "case_id": case_id,
        "runtime_metadata": runtime_metadata,
        "trajectory": trajectory,
    }
    return FrozenTrajectoryArtifact(
        artifact_schema_version="v1",
        canonical_hash=canonical_sha256(payload),
        case_id=case_id,
        runtime_metadata=runtime_metadata,
        trajectory=trajectory,
    )
