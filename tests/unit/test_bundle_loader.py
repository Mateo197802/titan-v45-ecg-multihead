from __future__ import annotations

from pathlib import Path

import pytest
import torch

from titan_v45.artifacts.manifest import sha256_file
from titan_v45.contracts.profiles import IncompatibleArtifactError, ModelProfile
from titan_v45.models.bundle import load_profile_bundle
from titan_v45.models.specialists import ClassWiseBinaryMLP


def _fixture_bundle(tmp_path: Path) -> tuple[ModelProfile, Path, Path, dict[str, object]]:
    backbone = tmp_path / "backbone.pt"
    specialist = tmp_path / "specialist.pt"
    torch.save({"model": {"weight": torch.ones(1)}, "parameter_count": 1}, backbone)
    model = ClassWiseBinaryMLP(input_dim=4, output_dim=2, hidden_dim=3)
    torch.save({"state_dict": model.state_dict()}, specialist)
    profile = ModelProfile(
        name="test_profile",
        task="rhythm",
        classes=("A", "B"),
        thresholds=(0.4, 0.6),
        canonical_status="TEST_ONLY",
        backbone_sha256=sha256_file(backbone),
        specialist_sha256=sha256_file(specialist),
        artifact_classes=("A", "B"),
    )
    contract: dict[str, object] = {
        "profile": profile.name,
        "task": profile.task,
        "classes": list(profile.classes),
        "artifact_classes": list(profile.artifact_classes),
        "backbone_rhythm_classes": list(profile.backbone_rhythm_classes),
        "backbone_pathology_classes": list(profile.backbone_pathology_classes),
        "thresholds": list(profile.thresholds),
        "backbone_sha256": profile.backbone_sha256,
        "specialist_sha256": profile.specialist_sha256,
        "backbone_parameter_count": 1,
    }
    return profile, backbone, specialist, contract


def test_load_profile_bundle_verifies_complete_contract(tmp_path: Path) -> None:
    profile, backbone, specialist, contract = _fixture_bundle(tmp_path)
    loaded = load_profile_bundle(profile, backbone, specialist, contract)
    assert loaded.specialist_architecture.input_dim == 4
    assert loaded.specialist_architecture.hidden_dim == 3
    assert loaded.specialist_architecture.output_dim == 2


@pytest.mark.parametrize(
    "field",
    [
        "profile",
        "task",
        "classes",
        "thresholds",
        "artifact_classes",
        "backbone_rhythm_classes",
        "backbone_pathology_classes",
    ],
)
def test_load_profile_bundle_rejects_incompatible_metadata(tmp_path: Path, field: str) -> None:
    profile, backbone, specialist, contract = _fixture_bundle(tmp_path)
    contract[field] = "wrong" if field in {"profile", "task"} else ["wrong"]
    with pytest.raises(IncompatibleArtifactError):
        load_profile_bundle(profile, backbone, specialist, contract)


def test_load_profile_bundle_rejects_modified_artifact(tmp_path: Path) -> None:
    profile, backbone, specialist, contract = _fixture_bundle(tmp_path)
    specialist.write_bytes(specialist.read_bytes() + b"modified")
    with pytest.raises(IncompatibleArtifactError, match="specialist hash"):
        load_profile_bundle(profile, backbone, specialist, contract)
