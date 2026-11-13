"""Compare two sealed SPH runs, exporting only aggregate reproducibility evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from collections import Counter
from pathlib import Path

PROFILES = ("P6", "P8", "P4")


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_ledger(ledger, receipt, protocol):
    meta = json.loads(receipt.read_text(encoding="utf-8"))
    baseline = protocol["frozen_baseline"]
    if (meta["ledger_sha256"] != digest(ledger)
            or meta["protocol_commit"] != baseline["implementation_commit"]
            or meta["protocol_sha256"] != baseline["protocol_sha256"]):
        raise ValueError("ledger or protocol receipt failed authentication")
    rows = {}
    with ledger.open(encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            key = row["record_id"]
            if key in rows:
                raise ValueError("duplicate record key in scoring ledger")
            rows[key] = row
    if len(rows) != baseline["expected_metadata_rows"]:
        raise ValueError("ledger does not cover the frozen denominator")
    status = dict(Counter(row["status"] for row in rows.values()))
    if status != meta["flow"]["status_counts"] or len(rows) != meta["flow"]["metadata_records"]:
        raise ValueError("ledger flow disagrees with sealed receipt")
    return rows, meta


def compare(old, new, tolerance):
    if not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError("invalid comparison tolerance")
    if old.keys() != new.keys():
        raise ValueError("record universes differ")
    flow = Counter(r["status"] for r in new.values())
    shared_scored = 0
    mismatches = 0
    fields = ("scores", "auxiliary_scores")
    results = {profile: {
        "decision_disagreements": 0,
        **{f: {"n": 0, "above_tolerance": 0, "maximum_absolute_difference": 0.0} for f in fields},
    } for profile in PROFILES}
    for key, after in new.items():
        before = old[key]
        mismatches += before["status"] != after["status"]
        if before["status"] != "scored" or after["status"] != "scored":
            continue
        shared_scored += 1
        if set(before["profiles"]) != set(PROFILES) or set(after["profiles"]) != set(PROFILES):
            raise ValueError("profile contract changed")
        for profile in PROFILES:
            a, b = before["profiles"][profile], after["profiles"][profile]
            target = results[profile]
            target["decision_disagreements"] += any(a[name] != b[name] for name in (
                "labels", "top1", "used_fallback", "threshold_crossings",
            ))
            for field in fields:
                if a[field].keys() != b[field].keys():
                    raise ValueError("score contract changed")
                metrics = target[field]
                for label, value in a[field].items():
                    delta = abs(value - b[field][label])
                    if not math.isfinite(delta):
                        raise ValueError("nonfinite score in paired ledgers")
                    metrics["n"] += 1
                    metrics["above_tolerance"] += delta > tolerance
                    metrics["maximum_absolute_difference"] = max(
                        metrics["maximum_absolute_difference"], delta,
                    )
    equivalent = (
        shared_scored == len(new) and shared_scored > 0 and mismatches == 0
        and all(not r["decision_disagreements"] and all(
            r[f]["n"] > 0 and not r[f]["above_tolerance"] for f in fields
        ) for r in results.values())
    )
    return {
        "total_records": len(new), "new_flow": dict(flow),
        "shared_scored_records": shared_scored, "flow_disagreements": mismatches,
        "profiles": results, "tolerance": tolerance, "strict_equivalence": equivalent,
        "scope": "SPH repeat inference only; not historical panel replay or independent validation",
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("protocol", "original-ledger", "original-receipt", "new-ledger", "new-receipt", "output"):
        p.add_argument(f"--{name}", type=Path, required=True)
    a = p.parse_args()
    protocol = json.loads(a.protocol.read_text(encoding="utf-8"))
    old, old_meta = load_ledger(a.original_ledger, a.original_receipt, protocol)
    new, new_meta = load_ledger(a.new_ledger, a.new_receipt, protocol)
    for key in ("source_sha256", "model_sha256", "private_duplicate_index_sha256"):
        if old_meta[key] != new_meta[key]:
            raise ValueError(f"immutable input mismatch: {key}")
    report = compare(old, new, protocol["replay"]["absolute_score_tolerance"])
    report.update({
        "audit_job": os.environ.get("SLURM_JOB_ID"),
        "experiment_protocol_sha256": digest(a.protocol),
        "original_receipt_sha256": digest(a.original_receipt),
        "new_receipt_sha256": digest(a.new_receipt),
        "original_ledger_sha256": old_meta["ledger_sha256"],
        "new_ledger_sha256": new_meta["ledger_sha256"],
        "record_identifiers_exported": False,
    })
    with a.output.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2, allow_nan=False)
        f.write("\n")


if __name__ == "__main__":
    main()
