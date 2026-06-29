from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import torch

from titan_v45.artifacts.manifest import sha256_file
from titan_v45.contracts.profiles import (
    IncompatibleArtifactError,
    ModelProfile,
    validate_artifact_compatibility,
)
from titan_v45.models.checkpoints import ClassWiseArchitecture, infer_classwise_architecture


@dataclass(frozen=True)
class LoadedProfileBundle:
    profile: ModelProfile
    backbone_checkpoint: Mapping[str, object]
    specialist_checkpoint: Mapping[str, object]
    specialist_architecture: ClassWiseArchitecture


def _require_equal(contract: Mapping[str, object], key: str, expected: object) -> None:
    actual = contract.get(key)
    if isinstance(expected, tuple):
        actual = tuple(actual) if isinstance(actual, (list, tuple)) else actual
    if actual != expected:
        raise IncompatibleArtifactError(
            f"bundle contract field {key!r} does not match the {expected!r} profile value"
        )


def _tensor_state_dict(
    checkpoint: Mapping[str, object], keys: tuple[str, ...]
) -> Mapping[str, torch.Tensor]:
    for key in keys:
        candidate = checkpoint.get(key)
        if isinstance(candidate, Mapping) and candidate:
            if all(torch.is_tensor(value) for value in candidate.values()):
                return candidate
    raise IncompatibleArtifactError(
        f"checkpoint has no tensor state_dict under any of: {', '.join(keys)}"
    )


def load_profile_bundle(
    profile: ModelProfile,
    backbone_path: str | Path,
    specialist_path: str | Path,
    contract: Mapping[str, object],
    *,
    map_location: str | torch.device = "cpu",
) -> LoadedProfileBundle:
    """Load a profile only after verifying the complete frozen release contract."""
    _require_equal(contract, "profile", profile.name)
    _require_equal(contract, "task", profile.task)
    _require_equal(contract, "classes", profile.classes)
    _require_equal(contract, "thresholds", profile.thresholds)
    _require_equal(contract, "artifact_classes", profile.artifact_classes)
    _require_equal(contract, "backbone_rhythm_classes", profile.backbone_rhythm_classes)
    _require_equal(contract, "backbone_pathology_classes", profile.backbone_pathology_classes)

    backbone_digest = sha256_file(backbone_path)
    specialist_digest = sha256_file(specialist_path)
    if contract.get("backbone_sha256") != backbone_digest:
        raise IncompatibleArtifactError("backbone hash does not match the bundle contract")
    if contract.get("specialist_sha256") != specialist_digest:
        raise IncompatibleArtifactError("specialist hash does not match the bundle contract")
    validate_artifact_compatibility(
        profile,
        backbone_sha256=backbone_digest,
        specialist_sha256=specialist_digest,
        classes=profile.classes,
        thresholds=profile.thresholds,
    )

    backbone = torch.load(backbone_path, map_location=map_location, weights_only=True)
    specialist = torch.load(specialist_path, map_location=map_location, weights_only=True)
    if not isinstance(backbone, Mapping) or not isinstance(specialist, Mapping):
        raise IncompatibleArtifactError("both checkpoints must contain mapping payloads")
    specialist_keys = (
        ("pathology4_specialist_state_dict", "state_dict", "specialist_state_dict")
        if profile.task == "pathology"
        else ("rhythm_specialist_state_dict", "state_dict", "specialist_state_dict")
    )
    specialist_state = _tensor_state_dict(specialist, specialist_keys)
    architecture = infer_classwise_architecture(specialist_state)
    if architecture.output_dim != len(profile.artifact_classes):
        raise IncompatibleArtifactError(
            "specialist output width does not match the artifact class order"
        )
    checkpoint_rhythm_classes = tuple(backbone.get("primary8_classes", ()))
    checkpoint_pathology_classes = tuple(backbone.get("pathology4_classes", ()))
    if profile.backbone_rhythm_classes and checkpoint_rhythm_classes:
        if checkpoint_rhythm_classes != profile.backbone_rhythm_classes:
            raise IncompatibleArtifactError("backbone rhythm class order does not match profile")
    if profile.backbone_pathology_classes and checkpoint_pathology_classes:
        if checkpoint_pathology_classes != profile.backbone_pathology_classes:
            raise IncompatibleArtifactError("backbone pathology class order does not match profile")
    specialist_artifact_classes = tuple(
        specialist.get("pathology4_classes" if profile.task == "pathology" else "primary8_classes", ())
    )
    if specialist_artifact_classes and specialist_artifact_classes != profile.artifact_classes:
        raise IncompatibleArtifactError("specialist class order does not match profile")
    expected_parameters = contract.get("backbone_parameter_count")
    observed_parameters = backbone.get("parameter_count")
    if observed_parameters is not None and expected_parameters is not None:
        if int(observed_parameters) != int(expected_parameters):
            raise IncompatibleArtifactError("backbone parameter count does not match contract")
    return LoadedProfileBundle(profile, backbone, specialist, architecture)
