from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from titan_v45.artifacts.release import (
    REJECTED_A10_HASHES,
    audit_release_hashes,
    validate_release_manifest_hashes,
)

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("payload", [None, [], {}, {"assets": []}])
def test_rejects_missing_or_invalid_manifest_objects(payload: object) -> None:
    with pytest.raises(ValueError, match="manifest"):
        validate_release_manifest_hashes(payload)


def _payload() -> dict:
    digest = hashlib.sha256(b"model").hexdigest()
    return {"assets": [{"name": "model.pt", "path": "models/model.pt", "category": "model",
                        "bytes": 5, "sha256": digest}], "artifacts": {"models/model.pt": digest}}


def _write(root: Path, *, physical: bool = False) -> None:
    (root / "release-manifest.json").write_text(json.dumps(_payload()), encoding="utf-8")
    if physical:
        (root / "models").mkdir()
        (root / "models/model.pt").write_bytes(b"model")


@pytest.mark.parametrize("digest", sorted(REJECTED_A10_HASHES) + ["0" * 64, "f" * 64, "g" * 64, "abcd"])
def test_rejects_all_submitted_example_hashes_and_invalid_digests(digest: str) -> None:
    payload = _payload()
    payload["assets"][0]["sha256"] = digest
    with pytest.raises(ValueError, match="SHA-256"):
        validate_release_manifest_hashes(payload)


@pytest.mark.parametrize("size", [0, -1, True, "5", None])
def test_rejects_invalid_or_zero_byte_sizes(size: object) -> None:
    payload = _payload()
    payload["assets"][0]["bytes"] = size
    with pytest.raises(ValueError, match="asset bytes"):
        validate_release_manifest_hashes(payload)


def test_rejects_duplicate_assets_and_contradictory_hash_map() -> None:
    payload = _payload()
    payload["assets"].append(dict(payload["assets"][0]))
    with pytest.raises(ValueError, match="duplicate"):
        validate_release_manifest_hashes(payload)
    payload = _payload()
    payload["artifacts"] = {}
    with pytest.raises(ValueError, match="map disagrees"):
        validate_release_manifest_hashes(payload)


def test_no_physical_files_is_not_reported_as_physical_verification(tmp_path: Path) -> None:
    _write(tmp_path)
    result = audit_release_hashes(tmp_path)
    assert result["declarations_valid"] is True
    assert result["physical_assets_verified"] == []
    assert result["all_physical_assets_verified"] is False
    assert result["missing_physical_assets"] == ["model.pt"]
    with pytest.raises(ValueError, match="required model is missing"):
        audit_release_hashes(tmp_path, require_models=True)


def test_checks_actual_file_bytes_and_hash_not_only_declarations(tmp_path: Path) -> None:
    _write(tmp_path, physical=True)
    result = audit_release_hashes(tmp_path, require_models=True)
    assert result["all_physical_assets_verified"] is True
    assert result["physical_assets_verified"][0]["bytes"] == 5
    (tmp_path / "models/model.pt").write_bytes(b"other")
    with pytest.raises(ValueError, match="size/hash mismatch"):
        audit_release_hashes(tmp_path)


def test_correct_hash_with_wrong_declared_size_also_fails(tmp_path: Path) -> None:
    _write(tmp_path, physical=True)
    payload = _payload()
    payload["assets"][0]["bytes"] = 6
    (tmp_path / "release-manifest.json").write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="size/hash mismatch"):
        audit_release_hashes(tmp_path)


def test_rejects_path_escape() -> None:
    payload = _payload()
    payload["assets"][0]["path"] = "../model.pt"
    with pytest.raises(ValueError, match="escapes root"):
        validate_release_manifest_hashes(payload)


def test_tracked_release_declarations_agree_with_cedia_recovery_model_inventory() -> None:
    release = json.loads((ROOT / "release-manifest.json").read_text())
    recovery = json.loads((ROOT / "outputs/results/revision_20261028/cedia_artifact_recovery.json").read_text())
    validate_release_manifest_hashes(release)
    models = {asset["name"]: asset for asset in release["assets"] if asset["category"] == "model"}
    assert len(models) == len(recovery["weights"]) == 5
    for measured in recovery["weights"]:
        declared = models[measured["name"]]
        assert measured["bytes"] == declared["bytes"] > 0
        assert measured["sha256"] == declared["sha256"]
