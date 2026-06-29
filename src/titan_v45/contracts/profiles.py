from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


class IncompatibleArtifactError(ValueError):
    """Raised when artifacts do not satisfy a frozen model profile."""


@dataclass(frozen=True)
class ModelProfile:
    name: str
    task: str
    classes: tuple[str, ...]
    thresholds: tuple[float, ...]
    canonical_status: str
    backbone_sha256: str
    specialist_sha256: str
    evaluation_scope: str = "external_dev"
    artifact_classes: tuple[str, ...] = ()
    backbone_rhythm_classes: tuple[str, ...] = ()
    backbone_pathology_classes: tuple[str, ...] = ()


V3F_SHA256 = "ca5d4dcb4b9828e6c4339800fe81ec27f32d9b09a090bb57503bfb56746a8da8"
P6_SPECIALIST_SHA256 = "9c5a9265a7155e1206c551cc4e6d645b86363ba3dbdeb7baf7b9f173c314be3d"
P8_V3Q_SPECIALIST_SHA256 = "b30cb2bbb45f1231c93ff1c196aa966b57b49831cadb296131c0283e7b0ceb02"
P4_V3AG_BACKBONE_SHA256 = "bf71e4cf8acc34031cb3611c7031e0649822e705fd7dcea354a3ea583ce920ee"
P4_V3AG_SPECIALIST_SHA256 = "cf5091e962fffb3254b1a71fe57236dd82ea0139093df192511499d931391dbc"


CANONICAL_PROFILES: dict[str, ModelProfile] = {
    "rhythm_primary8": ModelProfile(
        name="rhythm_primary8",
        task="rhythm",
        classes=("AFIB", "SB", "STACH", "NSR", "RBBB", "PAC", "1AVB", "PVC"),
        thresholds=(0.800, 0.550, 0.800, 0.525, 0.725, 0.450, 0.775, 0.725),
        canonical_status="NO_PASA",
        backbone_sha256=V3F_SHA256,
        specialist_sha256=P8_V3Q_SPECIALIST_SHA256,
        artifact_classes=("AFIB", "SB", "STACH", "NSR", "RBBB", "PAC", "1AVB", "PVC"),
        backbone_rhythm_classes=("AFIB", "SB", "STACH", "NSR", "RBBB", "PAC", "1AVB", "PVC"),
        backbone_pathology_classes=("ASMI", "LVH", "IMI", "ISC_"),
    ),
    "rhythm_primary6_diagnostic": ModelProfile(
        name="rhythm_primary6_diagnostic",
        task="rhythm",
        classes=("AFIB", "SB", "STACH", "RBBB", "1AVB", "PVC"),
        thresholds=(0.820, 0.835, 0.775, 0.515, 0.570, 0.430),
        canonical_status="PASA_METRICA",
        backbone_sha256=V3F_SHA256,
        specialist_sha256=P6_SPECIALIST_SHA256,
        artifact_classes=("AFIB", "SB", "STACH", "NSR", "RBBB", "PAC", "1AVB", "PVC"),
        backbone_rhythm_classes=("AFIB", "SB", "STACH", "NSR", "RBBB", "PAC", "1AVB", "PVC"),
        backbone_pathology_classes=("ASMI", "LVH", "IMI", "ISC_"),
    ),
    "pathology_primary4": ModelProfile(
        name="pathology_primary4",
        task="pathology",
        classes=("ASMI", "LVH", "IMI", "ISC_"),
        thresholds=(0.670, 0.705, 0.635, 0.595),
        canonical_status="ACEPTADO_POR_DECISION_DEL_PROYECTO",
        backbone_sha256=P4_V3AG_BACKBONE_SHA256,
        specialist_sha256=P4_V3AG_SPECIALIST_SHA256,
        artifact_classes=("ASMI", "LVH", "IMI", "ISC_"),
        backbone_rhythm_classes=("NSR", "SB", "STACH", "RBBB", "PVC", "1AVB", "Flutter", "Paced"),
        backbone_pathology_classes=("ASMI", "LVH", "IMI", "ISC_"),
    ),
}


def validate_artifact_compatibility(
    profile: ModelProfile,
    *,
    backbone_sha256: str,
    specialist_sha256: str,
    classes: Sequence[str],
    thresholds: Sequence[float],
) -> None:
    if backbone_sha256.lower() != profile.backbone_sha256:
        raise IncompatibleArtifactError(f"backbone hash does not match {profile.name}")
    if specialist_sha256.lower() != profile.specialist_sha256:
        raise IncompatibleArtifactError(f"specialist hash does not match {profile.name}")
    if tuple(classes) != profile.classes:
        raise IncompatibleArtifactError(f"class order does not match {profile.name}")
    if tuple(float(value) for value in thresholds) != profile.thresholds:
        raise IncompatibleArtifactError(f"thresholds do not match {profile.name}")
