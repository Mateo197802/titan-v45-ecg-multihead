"""Reconstruct recorded membership decisions, not waveform inference or validation."""
from __future__ import annotations

import csv
import hashlib
import json
import math
from collections.abc import Mapping
from pathlib import Path


def membership_decision(
    probabilities: Mapping[str, float], thresholds: Mapping[str, float]
) -> dict[str, object]:
    """Use membership argmax; force that label only when no threshold passes.

    Mapping order is the declared class order and breaks exact score ties.
    """
    if not probabilities or probabilities.keys() != thresholds.keys():
        raise ValueError("probability and threshold class contracts must be equal and nonempty")
    if any(not math.isfinite(value) or not 0 <= value <= 1 for value in [*probabilities.values(), *thresholds.values()]):
        raise ValueError("probabilities and thresholds must be finite and in [0,1]")
    top1 = max(probabilities, key=probabilities.__getitem__)
    labels = [label for label, value in probabilities.items() if value >= thresholds[label]]
    return {"top1": top1, "labels": labels or [top1], "used_fallback": not labels}


def audit_saved_membership_policy(root: str | Path) -> dict[str, object]:
    root = Path(root)
    metrics_path = root / "outputs/results/external_dev/rhythm_primary8_metrics.json"
    rows_path = root / "outputs/results/external_dev/evidence/rhythm_primary8_record_predictions.csv"
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    classes = metrics["classes"]
    if len(set(classes)) != len(classes):
        raise ValueError("duplicate classes")
    thresholds = dict(zip(classes, metrics["thresholds"], strict=True))
    with rows_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("saved prediction table is empty")
    top1_matches = set_matches = fallback = raw_argmax_mismatches = 0
    for row in rows:
        result = membership_decision({name: float(row["membership_prob_" + name]) for name in classes}, thresholds)
        top1_matches += result["top1"] == row["predicted_label"]
        set_matches += set(result["labels"]) == set(row["predicted_labels"].split("|"))
        fallback += result["used_fallback"]
        raw_argmax_mismatches += max(classes, key=lambda name: float(row["prob_" + name])) != row["predicted_label"]
    return {"schema": "TITAN_V45_SAVED_MEMBERSHIP_POLICY_V1", "scope": "saved_decisions_not_waveform_inference",
            "records": len(rows), "top1_matches": top1_matches, "binary_set_matches": set_matches,
            "fallback_records": fallback, "other_score_stream_argmax_disagreements": raw_argmax_mismatches,
            "all_decisions_reconstructed": top1_matches == set_matches == len(rows),
            "rule": "argmax membership_prob; threshold membership_prob; if empty use membership argmax",
            "classes": classes, "thresholds": thresholds, "thresholds_modified": False,
            "reference_labels_used": False,
            "input_sha256_lf_normalized": {str(path.relative_to(root)).replace("\\", "/"): hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest() for path in [metrics_path, rows_path]},
            "limitations": ["Exact agreement with saved fields does not recover the original implementation or feature extraction.",
                            "This does not establish training isolation or independent external validation."]}
