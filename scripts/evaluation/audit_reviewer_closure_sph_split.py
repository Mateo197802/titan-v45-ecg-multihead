"""Reconcile sealed November calibration membership and cutoffs without references."""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from compare_reviewer_baseline import digest
from freeze_reviewer_selective_policy import calibration_member, components, freeze, jsonl
from score_reviewer_closure_ludb import PROTOCOL_SHA256, write_new


def audit_membership(index, split, recipe):
    groups = components(index)
    joined = {r["record_id"]: r for r in split}
    if len(joined) != len(split) or joined.keys() != groups.keys():
        raise ValueError("SPH split inventory does not reconcile")
    identifiers = defaultdict(lambda: defaultdict(set))
    counts = Counter()
    for r in index:
        key = r["ecg_id"]
        row = joined[key]
        group = groups[key]
        cal = calibration_member(group, recipe["split_seed"], recipe["calibration_fraction"])
        name = "calibration" if cal else "held"
        if row["component"] != group or row["split"] != name:
            raise ValueError("record was assigned to an unexpected split")
        counts[name] += 1
        for kind, value in (("patient", r["patient_id"]), ("signal", r["signal_sha256_canonical_f64"]),
                            ("component", group)):
            identifiers[kind][name].add(value)
    overlap = {kind: len(keys["calibration"] & keys["held"]) for kind, keys in identifiers.items()}
    if any(overlap.values()):
        raise ValueError("patient, exact signal or component overlap between splits")
    by_kind = {kind: {split_name: len(v) for split_name, v in keys.items()}
               for kind, keys in identifiers.items()}
    return groups, dict(counts), by_kind, overlap


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("closure", "phase", "baseline-config", "index", "split", "calibration", "joint",
                 "scoring-receipt", "ledger", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    if digest(args.closure) != PROTOCOL_SHA256:
        raise ValueError("closure protocol is not the frozen version")
    route = json.loads(args.closure.read_bytes())["route"]
    if digest(args.calibration) != route["calibration_policy_sha256"] or digest(args.joint) != route["policy_sha256"]:
        raise ValueError("frozen November policy digest mismatch")
    calibration = json.loads(args.calibration.read_bytes())
    joint = json.loads(args.joint.read_bytes())
    for path, field in ((args.phase, "phase_sha256"), (args.index, "duplicate_index_sha256"),
                        (args.split, "private_split_sha256"), (args.scoring_receipt, "scoring_receipt_sha256"),
                        (args.ledger, "scoring_ledger_sha256")):
        if digest(path) != calibration[field]:
            raise ValueError(f"immutable calibration input differs: {field}")
    phase = json.loads(args.phase.read_bytes())
    recipe = phase["development_selective_policy"]
    index = list(jsonl(args.index))
    groups, counts, supports, overlap = audit_membership(index, list(jsonl(args.split)), recipe)
    if len(index) != phase["frozen_baseline"]["expected_metadata_rows"]:
        raise ValueError("SPH calibration audit lacks the source denominator")
    scoring = json.loads(args.scoring_receipt.read_bytes())
    if digest(args.baseline_config) != scoring["protocol_sha256"]:
        raise ValueError("SPH release threshold config differs")
    thresholds = json.loads(args.baseline_config.read_bytes())["thresholds"]
    rebuilt = freeze(jsonl(args.ledger), groups, thresholds, recipe)
    for key, value in rebuilt.items():
        if calibration.get(key) != value:
            raise ValueError(f"November policy did not rederive exactly: {key}")
    if (joint["calibration_policy_sha256"] != digest(args.calibration)
            or joint["prior_private_split_sha256"] != digest(args.split)
            or joint["cutoffs"] != {p: rebuilt["policies"][p]["accept_at_or_above"] for p in ("P8", "P4")}
            or joint["additional_threshold_fit"] is not False
            or joint["reference_used_for_routing"] is not False):
        raise ValueError("joint policy is not the frozen calibration transport")
    write_new(args.output, {
        "schema": "TITAN_V45_CLOSURE_SPH_SPLIT_AUDIT_V1",
        "original_calibration_job": calibration["job"], "original_joint_job": route["policy_producer_job"],
        "eligible_ecgs": len(index), "ecg_by_split": counts, "distinct_by_split": supports,
        "overlap_calibration_held": overlap,
        "calibration_policy_sha256": digest(args.calibration), "joint_policy_sha256": digest(args.joint),
        "private_split_sha256": digest(args.split), "private_index_sha256": digest(args.index),
        "scoring_receipt_sha256": digest(args.scoring_receipt), "scoring_ledger_sha256": digest(args.ledger),
        "exact_calibration_recipe_rederived": True, "cutoffs": joint["cutoffs"],
        "references_read": False, "inference_run": False, "historical_independence_certified": False,
        "no_individual_records_exported": True,
    })


if __name__ == "__main__":
    main()
