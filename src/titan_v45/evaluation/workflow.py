"""Account for each input without consulting reference labels."""
from __future__ import annotations

import math
from collections import Counter
from collections.abc import Mapping

from titan_v45.evaluation.decision_policy import membership_decision
from titan_v45.uncertainty.quarantine import QuarantinePolicy, quarantine_decision


def route_record(
    rhythm: Mapping[str, float],
    rhythm_thresholds: Mapping[str, float],
    pathology: Mapping[str, tuple[float, float]],
    *,
    uncertainty: tuple[float, float, float] | None = None,
    policy: QuarantinePolicy | None = None,
) -> dict:
    """Return pre/post states; missing scores or policy do not imply clearance."""
    rhythm_result = membership_decision(rhythm, rhythm_thresholds) if rhythm else None
    for pair in pathology.values():
        if any(not math.isfinite(x) or not 0 <= x <= 1 for x in pair):
            raise ValueError("pathology scores and thresholds must be finite and in [0,1]")
    pathology_calls = {name: score >= threshold for name, (score, threshold) in pathology.items()}
    pre = ("both" if pathology else "rhythm_only") if rhythm else (
        "pathology_only" if pathology else "no_scores"
    )
    reasons: tuple[str, ...] = ()
    if uncertainty is not None:
        if policy is None or pre == "no_scores":
            raise ValueError("uncertainty requires an explicit policy and scored input")
        confidence, entropy, mi = uncertainty
        bounds = (confidence, entropy, mi, policy.min_confidence,
                  policy.max_predictive_entropy, policy.max_mutual_information)
        if any(not math.isfinite(x) or x < 0 for x in bounds) or max(
            confidence, policy.min_confidence
        ) > 1:
            raise ValueError("invalid uncertainty values or policy")
        decision = quarantine_decision(max_probability=confidence, predictive_entropy=entropy,
                                       mutual_information=mi, policy=policy)
        post = "quarantined" if decision.quarantined else "retained"
        reasons = decision.reasons
    else:
        post = "no_scores" if pre == "no_scores" else "quarantine_not_assessed"
    return {"pre": pre, "post": post, "rhythm": rhythm_result, "pathology": pathology_calls,
            "quarantine_reasons": reasons}


def summarize_routes(routes: Mapping[str, dict]) -> dict:
    if not routes:
        raise ValueError("input inventory is empty")
    pre = Counter(row["pre"] for row in routes.values())
    post = Counter(row["post"] for row in routes.values())
    transitions = Counter(f'{row["pre"]}->{row["post"]}' for row in routes.values())
    assessed = post["retained"] + post["quarantined"]
    complete = assessed == len(routes)
    return {"inputs": len(routes), "pre_counts": dict(sorted(pre.items())),
            "post_counts": dict(sorted(post.items())), "transitions": dict(sorted(transitions.items())),
            "quarantine_assessed": assessed,
            "quarantine_rate_among_assessed": post["quarantined"] / assessed if assessed else None,
            "quarantine_rate_all_inputs": post["quarantined"] / len(routes) if complete else None}
