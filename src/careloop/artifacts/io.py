"""Strict local loading for canonical frozen trajectory artifacts."""

from pathlib import Path

from careloop.artifacts.canonical import canonical_sha256
from careloop.artifacts.models import FrozenTrajectoryArtifact


class ArtifactError(ValueError):
    """Base class for artifact integrity failures outside domain validation."""


class ArtifactCanonicalEncodingError(ArtifactError):
    """Raised when stored JSON is valid but not in canonical byte form."""


class ArtifactHashMismatchError(ArtifactError):
    """Raised when stored and reconstructed content hashes differ."""


def load_frozen_trajectory_artifact(
    path: str | Path,
) -> FrozenTrajectoryArtifact:
    """Load one local artifact and verify encoding and content integrity."""
    artifact_path = Path(path)
    raw_bytes = artifact_path.read_bytes()
    raw_text = raw_bytes.decode("utf-8")
    artifact = FrozenTrajectoryArtifact.model_validate_json(raw_text)

    if raw_bytes != artifact.stored_bytes():
        raise ArtifactCanonicalEncodingError(
            f"artifact is not canonical UTF-8 JSON: {artifact_path}"
        )

    actual_hash = artifact.canonical_hash
    reconstructed_hash = canonical_sha256(artifact)
    if actual_hash != reconstructed_hash:
        raise ArtifactHashMismatchError(
            "artifact hash mismatch: "
            f"stored {actual_hash}, reconstructed {reconstructed_hash}"
        )
    return artifact
