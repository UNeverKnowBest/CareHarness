"""Purely offline reconstruction of frozen trajectory artifacts."""

from dataclasses import dataclass
from pathlib import Path

from careloop.artifacts import load_frozen_trajectory_artifact
from careloop.domain import Trajectory


@dataclass(frozen=True, slots=True)
class ReplayResult:
    """Reconstructed canonical evidence returned by deterministic replay."""

    canonical_bytes: bytes
    canonical_hash: str
    trajectory: Trajectory


def replay_artifact(path: str | Path) -> ReplayResult:
    """Replay from local bytes without adapters, models, network, or wall clock."""
    artifact = load_frozen_trajectory_artifact(path)
    return ReplayResult(
        canonical_bytes=artifact.canonical_payload_bytes(),
        canonical_hash=artifact.canonical_hash,
        trajectory=artifact.trajectory,
    )
