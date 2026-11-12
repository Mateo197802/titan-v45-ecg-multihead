"""Seal a label-blind SPH development policy without evaluating the held half."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

from compare_reviewer_baseline import PROFILES, digest


def components(index):
    """Link patients sharing an exact signal and return ECG -> component."""
    records, patients, owner = {}, {}, {}

    def find(p):
        while p != patients[p]:
            patients[p] = patients[patients[p]]
            p = patients[p]
        return p

    for row in index:
        key, p, signature = (row[k] for k in (
            "record_id", "patient_id", "signal_sha256_canonical_f64",
        ))
        if key in records or not p or not signature:
            raise ValueError("invalid duplicate-index row")
        records[key] = p
        patients.setdefault(p, p)
        a, b = sorted((find(p), find(owner.setdefault(signature, p))))
        patients[b] = a
    return {k: find(p) for k, p in records.items()}


def calibration_member(component, seed, fraction):
    key = json.dumps([seed, component], ensure_ascii=False, separators=(",", ":")).encode()
    ticket = int.from_bytes(hashlib.sha256(key).digest(), "big")
    numerator, denominator = Decimal(str(fraction)).as_integer_ratio()
    if not 0 < numerator < denominator:
        raise ValueError("invalid split fraction")
    return ticket * denominator < numerator * (1 << 256)


def confidence(scores, thresholds):
    if not scores or scores.keys() != thresholds.keys():
        raise ValueError("score and threshold contracts differ")
    if any(not math.isfinite(v) or not 0 <= v <= 1
           for v in (*scores.values(), *thresholds.values())):
        raise ValueError("probabilities and thresholds must be finite and in [0, 1]")
    return min(abs(value - thresholds[k]) for k, value in scores.items())


def cutoff(values, target):
    if not values or not 0 < target <= 1:
        raise ValueError("empty calibration set or invalid coverage")
    # Avoid binary-float off-by-one at integral quantile indices.
    j = int((1 - Decimal(str(target))) * len(values))
    return sorted(values)[j]


def freeze(rows, groups, thresholds, recipe):
    calibration = {g for g in set(groups.values()) if calibration_member(
        g, recipe["split_seed"], recipe["calibration_fraction"],
    )}
    values, seen, counts = defaultdict(list), set(), defaultdict(int)
    for row in rows:
        key = row["record_id"]
        if key in seen or key not in groups:
            raise ValueError("scoring ledger and component index do not reconcile")
        seen.add(key)
        if groups[key] not in calibration:
            # No labels or scores from the held partition influence calibration.
            counts["held_records"] += 1
            continue
        counts["calibration_records"] += 1
        if row["status"] != "scored":
            continue
        counts["calibration_scored"] += 1
        for profile in PROFILES:
            values[profile].append(confidence(row["profiles"][profile]["scores"], thresholds[profile]))
    if seen != groups.keys() or not counts["held_records"]:
        raise ValueError("incomplete ledger or empty held partition")
    policies = {}
    for p in PROFILES:
        c = cutoff(values[p], recipe["target_scored_coverage"])
        policies[p] = {
            "accept_at_or_above": c,
            "accepted_calibration": sum(v >= c for v in values[p]),
            "scored_calibration": len(values[p]),
        }
    return {
        "scope": "retrospective development policy; no independent validation",
        "target_scored_coverage": recipe["target_scored_coverage"],
        "counts": dict(counts),
        "calibration_components": len(calibration),
        "held_components": len(set(groups.values()) - calibration),
        "shared_components": 0,
        "policies": policies,
        "held_scores_used_for_selection": False,
        "reference_labels_used": False,
        "cascade_implemented": False,
    }


def jsonl(path):
    with path.open(encoding="utf-8") as f:
        for line in f:
            yield json.loads(line)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for n in ("phase", "frozen-config", "ledger", "receipt", "duplicate-index", "output"):
        p.add_argument(f"--{n}", type=Path, required=True)
    a = p.parse_args()
    phase = json.loads(a.phase.read_bytes())
    receipt = json.loads(a.receipt.read_bytes())
    baseline = phase["frozen_baseline"]
    if (receipt["protocol_commit"] != baseline["implementation_commit"]
            or receipt["protocol_sha256"] != baseline["protocol_sha256"]
            or digest(a.frozen_config) != baseline["protocol_sha256"]
            or digest(a.ledger) != receipt["ledger_sha256"]
            or digest(a.duplicate_index) != receipt["private_duplicate_index_sha256"]):
        raise ValueError("unsealed policy input")
    groups = components(jsonl(a.duplicate_index))
    if len(groups) != baseline["expected_metadata_rows"]:
        raise ValueError("incomplete component denominator")
    report = freeze(jsonl(a.ledger), groups, json.loads(a.frozen_config.read_bytes())["thresholds"],
                    phase["development_selective_policy"])
    report.update({
        "job": os.environ.get("SLURM_JOB_ID"),
        "phase_sha256": digest(a.phase),
        "scoring_receipt_sha256": digest(a.receipt),
        "duplicate_index_sha256": receipt["private_duplicate_index_sha256"],
        "scoring_ledger_sha256": receipt["ledger_sha256"],
    })
    with a.output.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2, allow_nan=False)
        f.write("\n")


if __name__ == "__main__":
    main()
