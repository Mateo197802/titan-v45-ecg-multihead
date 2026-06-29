from __future__ import annotations

from pathlib import Path

import pytest

from titan_v45.artifacts.manifest import ArtifactHashError, sha256_file, verify_artifact_manifest


def test_artifact_manifest_detects_hash_mismatch(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.bin"
    artifact.write_bytes(b"canonical")
    assert len(sha256_file(artifact)) == 64

    with pytest.raises(ArtifactHashError, match="artifact.bin"):
        verify_artifact_manifest(tmp_path, {"artifact.bin": "0" * 64})


def test_artifact_manifest_accepts_matching_hash(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.bin"
    artifact.write_bytes(b"canonical")
    verify_artifact_manifest(tmp_path, {"artifact.bin": sha256_file(artifact)})
