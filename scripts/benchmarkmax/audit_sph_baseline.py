"""Describe the already-observed V4.5 SPH baseline using aggregate bins only."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

ENDPOINTS = {"P6:AFIB": 50, "P8:PAC": 30, "P4:ASMI": 165, "P4:LVH": 142, "P4:IMI": 161}
BINS = 20


def digest(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def summarize(rows, expected):
    bins = [{"positive": 0, "negative": 0, "score_sum": 0.0} for _ in range(BINS)]
    counts = {"tp": 0, "tn": 0, "fp": 0, "fn": 0}
    for truth, decision, score in rows:
        if truth not in (0, 1) or decision not in (0, 1) or not math.isfinite(score) or not 0 <= score <= 1:
            raise ValueError("invalid input")
        bucket = bins[min(int(score * BINS), BINS - 1)]
        bucket["positive" if truth else "negative"] += 1
        bucket["score_sum"] += score
        counts[{(1, 1): "tp", (0, 0): "tn", (0, 1): "fp", (1, 0): "fn"}[(truth, decision)]] += 1
    if any(counts[key] != expected[key] for key in counts) or len(rows) != expected["rows"]:
        raise ValueError("frozen aggregate confusion counts do not match")
    positive, negative = counts["tp"] + counts["fn"], counts["tn"] + counts["fp"]
    for bucket in bins:
        count = bucket["positive"] + bucket["negative"]
        bucket["mean_score"] = bucket.pop("score_sum") / count if count else None
        bucket["statement_fraction"] = bucket["positive"] / count if count else None
    positives_seen = negatives_seen = 0
    curve = []
    for index in range(BINS - 1, -1, -1):
        positives_seen += bins[index]["positive"]
        negatives_seen += bins[index]["negative"]
        predicted = positives_seen + negatives_seen
        curve.append({"threshold_lower_edge": index / BINS,
                      "sensitivity": positives_seen / positive if positive else None,
                      "false_positive_rate": negatives_seen / negative if negative else None,
                      "precision": positives_seen / predicted if predicted else None})
    return {"records": len(rows), "positive_statements": positive, "negative_statements": negative,
            "statement_prevalence": positive / len(rows) if rows else None,
            "average_precision_no_skill_baseline": positive / len(rows) if rows else None,
            "frozen_decisions": counts,
            "frozen_auroc": expected["auroc"], "frozen_average_precision": expected["average_precision"],
            "frozen_brier": expected["brier_score"], "frozen_ece": expected["ece"],
            "score_bins_uniform_20": bins, "exploratory_binned_threshold_curve": curve}


def audit(metadata, ledger, aggregate):
    references, patients = {}, set()
    with Path(metadata).open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            record = row["ECG_ID"]
            if record in references:
                raise ValueError("duplicate metadata ID")
            if not row["Patient_ID"].strip():
                raise ValueError("missing patient identifier")
            patients.add(row["Patient_ID"].strip())
            references[record] = {int(statement.split("+")[0]) for statement in row["AHA_Code"].split(";")}
    outputs = {name: [] for name in ENDPOINTS}
    seen = set()
    with Path(ledger).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            record = row["record_id"]
            if record in seen or record not in references:
                raise ValueError("ledger identity mismatch")
            seen.add(record)
            if row["status"] != "scored":
                continue
            for name, code in ENDPOINTS.items():
                profile, target = name.split(":")
                prediction = row["profiles"][profile]
                outputs[name].append((int(code in references[record]), int(target in prediction["labels"]),
                                      float(prediction["scores"][target])))
    if seen != references.keys():
        raise ValueError("incomplete source population")
    return {"schema": "TITAN_V46_SPH_OBSERVED_BASELINE_DIAGNOSTIC_V1",
            "scope": "exploratory previously observed SPH; not independent confirmation",
            "reference": "documented ECG statement; absence is not adjudicated disease absence",
            "source_records": len(references), "source_patients": len(patients),
            "binning": "20 uniform score bins; threshold curves are binned approximations, not tuning",
            "endpoints": {name: summarize(rows, aggregate["endpoints"][name]["metrics"])
                          for name, rows in outputs.items()},
            "individual_records_exported": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("metadata", "ledger", "aggregate", "scoring-receipt", "output"):
        parser.add_argument(f"--{name}", required=True, type=Path)
    args = parser.parse_args()
    if digest(args.scoring_receipt) != "8abdc5f6561fc3fea77eeb68e8aa34bc2d02396cad9c2e9fbeea70b4188dac92":
        raise ValueError("scoring receipt hash mismatch")
    receipt = json.loads(args.scoring_receipt.read_text(encoding="utf-8"))
    if digest(args.metadata) != receipt["source_sha256"]["metadata.csv"]:
        raise ValueError("metadata hash mismatch")
    if digest(args.ledger) != receipt["ledger_sha256"]:
        raise ValueError("ledger hash mismatch")
    if digest(args.aggregate) != "09f93d9f310baaca672a33b0f369593cd88835a8ef08dc9929945c57cf18c988":
        raise ValueError("baseline aggregate hash mismatch")
    result = audit(args.metadata, args.ledger, json.loads(args.aggregate.read_text(encoding="utf-8")))
    result["inputs"] = {"metadata_sha256": digest(args.metadata), "ledger_sha256": digest(args.ledger),
                        "aggregate_sha256": digest(args.aggregate), "scoring_receipt_sha256": digest(args.scoring_receipt),
                        "script_sha256": digest(__file__)}
    with args.output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
        handle.write("\n")


if __name__ == "__main__":
    main()
