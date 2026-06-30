from __future__ import annotations

import pytest

from titan_v45.contracts.profiles import (
    CANONICAL_PROFILES,
    IncompatibleArtifactError,
    validate_artifact_compatibility,
)


def test_canonical_profile_contracts_are_explicit() -> None:
    primary8 = CANONICAL_PROFILES["rhythm_primary8"]
    primary6 = CANONICAL_PROFILES["rhythm_primary6_diagnostic"]
    pathology4 = CANONICAL_PROFILES["pathology_primary4"]

    assert primary8.classes == (
        "AFIB", "SB", "STACH", "NSR", "RBBB", "PAC", "1AVB", "PVC"
    )
    assert primary8.release_role == "primary8_candidate"
    assert primary6.classes == ("AFIB", "SB", "STACH", "RBBB", "1AVB", "PVC")
    assert primary6.artifact_classes == primary8.classes
    assert primary6.release_role == "primary6_diagnostic"
    assert pathology4.classes == ("ASMI", "LVH", "IMI", "ISC_")
    assert pathology4.release_role == "primary4_pathology"


def test_profile_rejects_incompatible_backbone_or_specialist() -> None:
    profile = CANONICAL_PROFILES["pathology_primary4"]

    with pytest.raises(IncompatibleArtifactError, match="backbone"):
        validate_artifact_compatibility(
            profile,
            backbone_sha256="ca5d4f46da9d8e6c4339800fe81ec27f32d9b09a090bb57503bfb56746a8da8",
            specialist_sha256=profile.specialist_sha256,
            classes=profile.classes,
            thresholds=profile.thresholds,
        )

    with pytest.raises(IncompatibleArtifactError, match="class order"):
        validate_artifact_compatibility(
            profile,
            backbone_sha256=profile.backbone_sha256,
            specialist_sha256=profile.specialist_sha256,
            classes=tuple(reversed(profile.classes)),
            thresholds=profile.thresholds,
        )
