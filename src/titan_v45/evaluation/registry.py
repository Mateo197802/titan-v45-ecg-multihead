from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CanonicalResult:
    profile: str
    accuracy: float
    macro_f1: float
    canonical_status: str
    coverage: float = 1.0
    records: int | None = None
    per_class_f1: dict[str, float] = field(default_factory=dict)
    scope: str = "external_dev"


CANONICAL_RESULTS: dict[str, CanonicalResult] = {
    "rhythm_primary8": CanonicalResult(
        profile="rhythm_primary8",
        accuracy=0.9060647514819882,
        macro_f1=0.7614253535094375,
        canonical_status="NO_PASA",
        records=2193,
        per_class_f1={
            "AFIB": 0.9183,
            "SB": 0.9426,
            "STACH": 0.9050,
            "NSR": 0.8342,
            "RBBB": 0.7769,
            "PAC": 0.4706,
            "1AVB": 0.6259,
            "PVC": 0.6180,
        },
    ),
    "rhythm_primary6_diagnostic": CanonicalResult(
        profile="rhythm_primary6_diagnostic",
        accuracy=0.9519172245891662,
        macro_f1=0.8009383239876123,
        canonical_status="PASA_METRICA",
        records=1643,
        per_class_f1={
            "AFIB": 0.9096,
            "SB": 0.9296,
            "STACH": 0.9069,
            "RBBB": 0.7774,
            "1AVB": 0.6258,
            "PVC": 0.6564,
        },
    ),
    "pathology_primary4": CanonicalResult(
        profile="pathology_primary4",
        accuracy=0.8022904853689048,
        macro_f1=0.793456370406346,
        canonical_status="ACEPTADO_POR_DECISION_DEL_PROYECTO",
        per_class_f1={
            "ASMI": 0.8122605363984674,
            "LVH": 0.6572769953051643,
            "IMI": 0.7887323943661971,
            "ISC_": 0.9155555555555555,
        },
    ),
}
