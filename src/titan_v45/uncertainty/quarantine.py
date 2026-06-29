from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QuarantinePolicy:
    min_confidence: float
    max_predictive_entropy: float
    max_mutual_information: float


@dataclass(frozen=True)
class QuarantineDecision:
    quarantined: bool
    reasons: tuple[str, ...]


def quarantine_decision(
    *,
    max_probability: float,
    predictive_entropy: float,
    mutual_information: float,
    policy: QuarantinePolicy,
) -> QuarantineDecision:
    reasons: list[str] = []
    if max_probability < policy.min_confidence:
        reasons.append("low_confidence")
    if predictive_entropy > policy.max_predictive_entropy:
        reasons.append("high_entropy")
    if mutual_information > policy.max_mutual_information:
        reasons.append("high_mutual_information")
    return QuarantineDecision(quarantined=bool(reasons), reasons=tuple(reasons))
