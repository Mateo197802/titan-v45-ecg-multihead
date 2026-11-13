"""Apply the prespecified joint P8/P4 route and reconcile all withheld positives."""
from __future__ import annotations

import argparse
import json
import math
import os
from collections import Counter, defaultdict
from pathlib import Path

from compare_reviewer_baseline import digest, load_ledger
from evaluate_reviewer_selective_policy import profile_stats, ratio
from freeze_reviewer_selective_policy import calibration_member, components, confidence, jsonl

JOINT = ("P8", "P4")


def write_new(path, content):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(content, stream, indent=2, allow_nan=False)
        stream.write("\n")


def classify(row, thresholds, cutoffs):
    if row["status"] != "scored":
        return {"route": "not_scored", "signed_margin": None, "profile_confidences": None, "emitted": None}
    values = {p: confidence(row["profiles"][p]["scores"], thresholds[p]) for p in JOINT}
    if any(not math.isfinite(cutoffs[p]) or not 0 <= cutoffs[p] <= 1 for p in JOINT):
        raise ValueError("invalid frozen joint cutoff")
    margin = min(v - cutoffs[p] for p, v in values.items())
    accepted = margin >= 0
    return {"route": "accepted" if accepted else "abstained", "signed_margin": margin,
            "profile_confidences": values, "uncertainty_index": 1-min(values.values()),
            "emitted": {p: row["profiles"][p]["labels"] for p in JOINT} if accepted else None}


def reconcile_prior(current, prior, cutoffs):
    if prior["status"] != current["status"]:
        raise ValueError("scoring status differs from prior route ledger")
    result = current["decision"]
    for p in JOINT:
        old = prior["profiles"][p]
        v = None if result["profile_confidences"] is None else result["profile_confidences"][p]
        expected = "not_scored" if v is None else "accepted" if v >= cutoffs[p] else "abstained"
        if old["route"] != expected or old["confidence"] != v:
            raise ValueError("prior profile route differs from score-only reconstruction")


def positive_accounting(stats):
    result = {}
    for label, e in stats["endpoints"].items():
        accepted, abstained = (e["routes"][r] for r in ("accepted", "abstained"))
        all_held = e["held_statement_positive"]
        base = e["routes"]["baseline"]
        if any(base[c] != accepted[c]+abstained[c] for c in ("tn", "fp", "fn", "tp", "n")):
            raise ValueError("paired route confusion counts do not reconcile")
        deferred = abstained["tp"]+abstained["fn"]
        missing = all_held - base["tp"]-base["fn"]
        if missing < 0 or sum((accepted["tp"], accepted["fn"], deferred, missing)) != all_held:
            raise ValueError("positive statement flow does not reconcile")
        result[label] = {
            "held_statement_positives": all_held,
            "accepted_emitted_correct_positive": accepted["tp"],
            "accepted_emitted_missed_positive": accepted["fn"],
            "abstained_reference_positive_no_prediction": deferred,
            "technically_unscored_reference_positive_no_prediction": missing,
            "abstained_baseline_counterfactual_fn": abstained["fn"],
            "fraction_of_held_statement_positives_correctly_emitted": ratio(accepted["tp"], all_held),
            "fraction_of_held_statement_positives_abstained": ratio(deferred, all_held),
        }
    return result


def source_stratum(codes, mapped):
    if not codes:
        return "missing_statement"
    if 1 in codes:
        return "normal_only" if codes == {1} else "ambiguous_normal_plus_other"
    if codes & mapped:
        return "mapped_statement_with_other" if codes - mapped else "mapped_statement_only"
    return "no_mapped_statement_not_normal"


def main():
    from titan_v45.data.sph import read_sph_dictionary, read_sph_metadata
    from titan_v45.evaluation.sph_report import _metric_values

    p = argparse.ArgumentParser(description=__doc__)
    for n in ("phase", "protocol", "frozen", "source", "ledger", "receipt", "duplicate-index",
              "selective-dir", "output-dir"):
        p.add_argument(f"--{n}", type=Path, required=True)
    a = p.parse_args()
    phase, protocol, frozen = (json.loads(path.read_bytes()) for path in (a.phase, a.protocol, a.frozen))
    if tuple(protocol["profiles_in_joint_route"]) != JOINT:
        raise ValueError("wrong joint-profile contract")
    rows, receipt = load_ledger(a.ledger, a.receipt, phase)
    policy_path, prior_path, split_path, prior_aggregate = (
        a.selective_dir / n for n in ("policy.json", "private-routes.jsonl", "private-split.jsonl", "aggregate.json"))
    policy, previous = (json.loads(path.read_bytes()) for path in (policy_path, prior_aggregate))
    if (previous["job"] != "33362" or policy["job"] != "33362"
            or digest(policy_path) != previous["policy_sha256"]
            or digest(prior_path) != previous["private_route_ledger_sha256"]
            or digest(split_path) != policy["private_split_sha256"]
            or digest(a.duplicate_index) != policy["duplicate_index_sha256"]
            or digest(a.receipt) != policy["scoring_receipt_sha256"]
            or receipt["ledger_sha256"] != policy["scoring_ledger_sha256"]
            or digest(a.frozen) != receipt["protocol_sha256"] or digest(a.phase) != policy["phase_sha256"]
            or policy["reference_labels_used"] is not False or policy["held_scores_used_for_selection"] is not False):
        raise ValueError("upstream selection receipt or original scoring lineage differs")
    cuts = {p: policy["policies"][p]["accept_at_or_above"] for p in JOINT}
    recipe = phase["development_selective_policy"]
    groups = components(jsonl(a.duplicate_index))
    held = {k for k, g in groups.items() if not calibration_member(g, recipe["split_seed"], recipe["calibration_fraction"])}
    splits = list(jsonl(split_path))
    if (rows.keys() != groups.keys() or len(splits) != len(groups)
            or len({r["record_id"] for r in splits}) != len(groups)
            or any(r["component"] != groups[r["record_id"]]
                   or r["split"] != ("held" if r["record_id"] in held else "calibration") for r in splits)
            or len(held) != policy["counts"]["held_records"]):
        raise ValueError("held membership does not reproduce sealed patient-component split")
    freeze = a.output_dir / "joint-policy.json"
    write_new(freeze, {"protocol_sha256": digest(a.protocol), "calibration_policy_sha256": digest(policy_path),
                       "prior_private_split_sha256": digest(split_path), "cutoffs": cuts, "joint_rule": protocol["route"],
                       "additional_threshold_fit": False, "reference_used_for_routing": False,
                       "prior_held_outcomes_used_for_rule_selection": False})
    prior_rows = list(jsonl(prior_path))
    prior = {r["record_id"]: r for r in prior_rows}
    if len(prior_rows) != len(prior) or prior.keys() != held:
        raise ValueError("upstream held route denominator differs")
    for n in ("metadata.csv", "code.csv"):
        if digest(a.source/n) != receipt["source_sha256"][n]:
            raise ValueError("source metadata changed")
    primary, mod = read_sph_dictionary((a.source/"code.csv").read_text(encoding="utf-8-sig"))
    refs = read_sph_metadata((a.source/"metadata.csv").read_text(encoding="utf-8-sig"), primary, mod)
    if refs.keys() != groups.keys():
        raise ValueError("source metadata denominator differs")
    e = [(item["profile"], item["name"], set(item["codes"])) for item in frozen["endpoints"] if item["profile"] in JOINT]
    names = [p+":"+c for p, c, _ in e]
    union = set().union(*(codes for _, _, codes in e))
    data, strata, driver = [], defaultdict(Counter), Counter()
    private = a.output_dir / "private-joint-routes.jsonl"
    with private.open("x", encoding="utf-8") as stream:
        for key in rows:
            if key not in held:
                continue
            row = rows[key]
            joint = classify(row, frozen["thresholds"], cuts)
            reconcile_prior({"status": row["status"], "decision": joint}, prior[key], cuts)
            scored = joint["route"] != "not_scored"
            stratum = source_stratum(refs[key].primary_codes, union)
            strata[stratum][joint["route"]] += 1
            if joint["route"] == "abstained":
                failures = [p for p in JOINT if joint["profile_confidences"][p] < cuts[p]]
                driver["+".join(failures)] += 1
            truth = [int(bool(codes & refs[key].primary_codes)) for _, _, codes in e]
            baseline = [int(c in row["profiles"][p]["labels"]) for p, c, _ in e] if scored else [0]*len(e)
            scores = [row["profiles"][p]["scores"][c] for p, c, _ in e] if scored else [0.0]*len(e)
            data.append({"component": groups[key], "route": joint["route"], "confidence": joint["signed_margin"] or 0,
                         "reference": truth, "decision": baseline, "scores": scores})
            stream.write(json.dumps({
                "record_id": key, "route": joint, "technical_status": row["status"],
                "original_predictions": {p: row["profiles"][p] for p in JOINT} if scored else None,
                "statement_reference": dict(zip(names, truth, strict=True)), "reference_eligible": names,
                "second_stage_prediction": None,
                "counterfactual_baseline_confusion": {
                    n: ("TP" if y and c else "FN" if y else "FP" if c else "TN") if scored else None
                    for n, y, c in zip(names, truth, baseline, strict=True)
                },
            }, separators=(",", ":"), allow_nan=False)+"\n")
    stats = profile_stats(data, names, _metric_values, protocol["intervals"])
    write_new(a.output_dir/"aggregate.json", {
        "scope": protocol["scope"], "job": os.environ.get("SLURM_JOB_ID"),
        "joint_policy_sha256": digest(freeze), "private_joint_route_ledger_sha256": digest(private),
        "source_stratum_route_counts": dict(strata), "abstention_drivers": dict(driver), "joint_metrics": stats,
        "positive_statement_disposition": positive_accounting(stats), "cascade": protocol["cascade"],
        "risk": protocol["risk"], "record_identifiers_exported": False, "independent_validation": False,
    })


if __name__ == "__main__":
    main()
