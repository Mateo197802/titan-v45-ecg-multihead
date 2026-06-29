from __future__ import annotations

import hashlib
from collections.abc import Mapping
from pathlib import Path


class ArtifactHashError(RuntimeError):
    """Raised when a release artifact is missing or has an unexpected digest."""


def sha256_file(path: str | Path, *, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_artifact_manifest(root: str | Path, artifacts: Mapping[str, str]) -> None:
    base = Path(root).resolve()
    for relative_path, expected in artifacts.items():
        candidate = (base / relative_path).resolve()
        if not candidate.is_relative_to(base):
            raise ArtifactHashError(f"artifact escapes root: {relative_path}")
        if not candidate.is_file():
            raise ArtifactHashError(f"artifact is missing: {relative_path}")
        actual = sha256_file(candidate)
        if actual.lower() != expected.lower():
            raise ArtifactHashError(
                f"artifact hash mismatch for {relative_path}: expected {expected}, got {actual}"
            )
