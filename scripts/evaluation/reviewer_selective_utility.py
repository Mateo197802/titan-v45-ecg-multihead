"""Compare fixed routing policies without exporting individual records."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path

import numpy as np

from compare_reviewer_baseline import digest
from evaluate_reviewer_closure_ludb import KNOWN
from freeze_reviewer_selective_policy import confidence, jsonl
from score_reviewer_closure_ludb import route, write_new

JOINT = ("P8", "P4")
SEALED = {
    "joint": "95f2f6749ed3837c38eddfd2770689edac7adccf73fb3e160cfff07560727172",
    "calibration": "61a4cfafb30621991288ab1a314ef932650ab27bbfd8ff0cacb1ff5a5633209b",
    "ludb": "af72ae7bf04c807a88ea33db3076970aac780c3f7669b145b34b34c64cf87c29",
    "ludb_score": "73e5a4a9944a03c2c4a549f80e8ae9fa280d328f31fc925b910385ed8aac41c4",
}


def sealed(path, expected):
    if digest(path) != expected:
        raise ValueError(f"seal mismatch: {path.name}")
    return path


def read(path):
    return json.loads(path.read_bytes())


def load(base, sph_config_path):
    phase = base / "titan-four-reviewers-november-phase1"
    closure = base / "titan-v45-scientific-closure"
    joint = phase / "joint-selective-33414"
    cal = phase / "selective-33362"
    lu = closure / "ludb-eval-33720"
    aggregate = read(sealed(joint / "aggregate.json", SEALED["joint"]))
    policy = read(sealed(joint / "joint-policy.json", aggregate["joint_policy_sha256"]))
    calibration = read(sealed(cal / "policy.json", SEALED["calibration"]))
    splits = list(jsonl(sealed(cal / "private-split.jsonl", policy["prior_private_split_sha256"])))
    if (policy["calibration_policy_sha256"] != SEALED["calibration"]
            or policy["reference_used_for_routing"] or policy["additional_threshold_fit"]
            or policy["prior_held_outcomes_used_for_rule_selection"]
            or calibration["reference_labels_used"] or calibration["held_scores_used_for_selection"]
            or policy["cutoffs"] != {p: calibration["policies"][p]["accept_at_or_above"] for p in JOINT}
            or {r["component"] for r in splits if r["split"] == "calibration"}
            & {r["component"] for r in splits if r["split"] == "held"}
            or len({r["record_id"] for r in splits}) != len(splits)):
        raise ValueError("calibration and held lineage not verified")
    held = {r["record_id"]: r["component"] for r in splits if r["split"] == "held"}
    sph_receipt_path = phase / "sph-frozen-33355" / "scoring-receipt.json"
    sph_receipt = read(sealed(sph_receipt_path, calibration["scoring_receipt_sha256"]))
    sph_config = read(sealed(sph_config_path, sph_receipt["protocol_sha256"]))
    sph_rows = list(jsonl(sealed(joint / "private-joint-routes.jsonl",
                                 aggregate["private_joint_route_ledger_sha256"])))
    if len(sph_rows) != len(held) or {r["record_id"] for r in sph_rows} != set(held):
        raise ValueError("SPH denominator differs")
    sph_endpoints = [(e["profile"], e["name"]) for e in sph_config["endpoints"] if e["profile"] in JOINT]
    sph = []
    for r in sph_rows:
        pred = r["original_predictions"]
        actual = r["route"]
        if pred is None:
            if actual["route"] != "not_scored" or actual["emitted"] is not None:
                raise ValueError("invalid SPH technical status")
        else:
            values = {p: confidence(pred[p]["scores"], sph_config["thresholds"][p]) for p in JOINT}
            margin = min(values[p] - policy["cutoffs"][p] for p in JOINT)
            expected = {p: pred[p]["labels"] for p in JOINT} if margin >= 0 else None
            if (actual["route"] != ("accepted" if margin >= 0 else "abstained")
                    or actual["signed_margin"] != margin or actual["profile_confidences"] != values
                    or actual["emitted"] != expected or r["second_stage_prediction"] is not None):
                raise ValueError("SPH label-free route mismatch")
        truth = [r["statement_reference"][f"{p}:{c}"] for p, c in sph_endpoints]
        sph.append((r["record_id"], held[r["record_id"]], pred, actual["signed_margin"], truth))
    l_agg = read(sealed(lu / "aggregate.json", SEALED["ludb"]))
    l_score = read(sealed(closure / "ludb-score-33697" / "scoring-receipt.json", SEALED["ludb_score"]))
    if (l_score["reference_values_used"] or l_score["route_reference_values_used"]
            or l_score["policy_sha256"] != aggregate["joint_policy_sha256"]):
        raise ValueError("LUDB scoring lineage differs")
    original = list(jsonl(sealed(closure / "ludb-score-33697" / "private-scored-and-routed.jsonl",
                                 l_score["private_score_route_ledger_sha256"])))
    by_key = {r["key"]: r for r in original}
    l_rows = list(jsonl(sealed(lu / "private-reference-route-ledger.jsonl",
                               l_agg["private_reference_route_ledger_sha256"])))
    if len(by_key) != len(original) or len(l_rows) != len(by_key) or {r["key"] for r in l_rows} != set(by_key):
        raise ValueError("LUDB denominator differs")
    lu_endpoints = [(p, c) for p in JOINT for c in l_score["thresholds"][p]]
    ludb = []
    for r in l_rows:
        actual = route(r["profiles"], l_score["thresholds"], policy)
        before = by_key[r["key"]]
        if actual != r["route"] or actual != before["route"] or r["profiles"] != before["profiles"]:
            raise ValueError("LUDB route mismatch")
        pred = None if actual["state"] == "technical_unscored" else r["profiles"]
        truth = [KNOWN.get(r["references"][c], -1) for _, c in lu_endpoints]
        ludb.append((r["key"], r["component"], pred, actual["signed_margin"], truth))
    return {"SPH": (sph, sph_endpoints, sph_config["thresholds"]),
            "LUDB": (ludb, lu_endpoints, l_score["thresholds"])}, policy


def ratio(n, d):
    return float(n / d) if d else None


def entropy(p):
    p = np.clip(p, 1e-15, 1 - 1e-15)
    return -np.mean(p * np.log(p) + (1 - p) * np.log1p(-p))


def take_k(rank, keys, k):
    order = np.lexsort((keys, -rank))
    accepted = np.zeros(len(rank), dtype=bool)
    accepted[order[:k]] = True
    return accepted


def cumulative_risk(rank, errors, known):
    order = np.argsort(-rank, kind="stable")
    ends = np.r_[np.flatnonzero(np.diff(rank[order])), len(order) - 1]
    coverage = (ends + 1) / len(order)
    e, d = np.cumsum(errors[order])[ends], np.cumsum(known[order])[ends]
    risk = [ratio(a, b) for a, b in zip(e, d, strict=True)]
    area = None if None in risk else float(np.diff(np.r_[0, coverage]) @ risk)
    curve = [{"coverage": float(coverage[i]), "risk": risk[i]} for i in np.unique(
        np.r_[np.minimum(np.searchsorted(coverage, np.linspace(0.05, 1, 20)), len(ends)-1), len(ends)-1])]
    return area, curve


def paired_ci(group, er, kn, frozen, recipe):
    counts = np.column_stack((er, kn, er * frozen, kn * frozen))
    groups = np.zeros((group.max() + 1, counts.shape[1]))
    np.add.at(groups, group, counts)
    rng = np.random.default_rng(recipe["bootstrap_seed"])
    contrasts = []
    for n in range(0, recipe["replicates"], 32):
        idx = rng.integers(len(groups), size=(min(32, recipe["replicates"]-n), len(groups)))
        e, d, ea, da = groups[idx].sum(axis=1).T
        ok = (d > 0) & (da > 0)
        contrasts.extend((ea[ok] / da[ok] - e[ok] / d[ok]).tolist())
    if len(contrasts) < recipe["replicates"] * 0.95:
        raise ValueError("insufficient valid bootstrap replicates")
    return {"replicates_valid": len(contrasts), "ci95": np.quantile(contrasts, [.025, .975]).tolist(),
            "ci98_75": np.quantile(contrasts, [.00625, .99375]).tolist()}


def evaluate(rows, endpoints, thresholds, recipe):
    scored = [r for r in rows if r[2] is not None]
    keys = np.array([sha256(("titan-utility-v1:" + r[0]).encode()).hexdigest() for r in scored])
    _, groups = np.unique([r[1] for r in scored], return_inverse=True)
    y = np.array([r[4] for r in scored])
    known = y != -1
    pos, neg = y == 1, y == 0
    calls = np.array([[c in r[2][p]["labels"] for p, c in endpoints] for r in scored])
    tp, fp, fn, tn = (calls & pos), (calls & neg), (~calls & pos), (~calls & neg)
    er, kn = (fp | fn).sum(axis=1), known.sum(axis=1)
    margin = np.array([r[3] for r in scored])
    distance = np.array([min(confidence(r[2][p]["scores"], thresholds[p]) for p in JOINT) for r in scored])
    uncertainty = np.array([-entropy([x for p in JOINT for x in r[2][p]["scores"].values()]) for r in scored])
    frozen = margin >= 0
    k, n = int(frozen.sum()), len(scored)
    rules = dict(zip(recipe["rules"], (np.ones(n), frozen, take_k(distance, keys, k),
                                      take_k(uncertainty, keys, k), np.full(n, k/n)), strict=True))
    stats = {}
    for name, w in rules.items():
        err, den = float(w @ er), float(w @ kn)
        unknown = kn.sum() - den
        endpoint_rows = {}
        for j, (p, c) in enumerate(endpoints):
            a, b, d, e = (float(w @ z[:, j]) for z in (tp, fp, fn, tn))
            unresolved = float((1-w) @ pos[:, j])
            endpoint_rows[f"{p}:{c}"] = {
                "tp": a, "fp": b, "fn_emitted": d, "tn": e, "positive_withheld": unresolved,
                "positive_total": int(pos[:, j].sum()), "negative_total": int(neg[:, j].sum()),
                "positive_technical_unscored": sum(int(r[4][j] == 1) for r in rows if r[2] is None),
                "accepted_sensitivity": ratio(a, a+d), "accepted_specificity": ratio(e, e+b),
                "full_scored_sensitivity": ratio(a, a+d+unresolved), "ppv": ratio(a, a+b), "npv": ratio(e, e+d),
            }
        stats[name] = {"accepted": float(w.sum()), "coverage_scored": float(w.mean()),
                       "coverage_full": ratio(w.sum(), len(rows)), "emitted_errors": err,
                       "known_emitted": den, "known_withheld": float(unknown),
                       "accepted_risk": ratio(err, den), "withheld_errors": float(er.sum()-err),
                       "withheld_correct": float(unknown - (er.sum()-err)),
                       "withheld_risk": ratio(er.sum()-err, unknown),
                       "withheld_positive": float((1-w) @ pos.sum(axis=1)),
                       "full_scored_cost": {str(l): ratio(err+l*unknown, kn.sum()) for l in recipe["loss_weights"]},
                       "break_even_vs_no_abstention": ratio(er.sum()-err, unknown), "endpoints": endpoint_rows}
    ranking = {}
    for name, r in zip(recipe["rules"][1:4], (margin, distance, uncertainty), strict=True):
        area, curve = cumulative_risk(r, er, kn)
        ranking[name] = {"aurc": area, "curve": curve}
    bins = []
    for lo, hi in zip(recipe["confidence_bins"][:-1], recipe["confidence_bins"][1:], strict=True):
        z = (margin >= lo) & (margin < hi if hi < 1 else margin <= hi)
        bins.append({"lower": lo, "upper": hi, "ecgs": int(z.sum()), "known": int(kn[z].sum()),
                     "observed_risk": ratio(er[z].sum(), kn[z].sum())})
    point = stats["frozen_joint"]["accepted_risk"] - stats["no_abstention"]["accepted_risk"]
    # For a randomized policy the ratio of expected counts equals the all-scored risk.
    return {"full_ecgs": len(rows), "technical_unscored": len(rows)-n, "scored_ecgs": n,
            "scored_clusters": len(set(groups)), "known_scored_opportunities": int(kn.sum()),
            "unknown_scored_opportunities": int(y.size-kn.sum()), "rules": stats, "ranking": ranking,
            "confidence_reliability_not_probability_calibration": bins,
            "paired_risk_difference_vs_no_abstention_and_random_expected": {
                "difference": point, **paired_ci(groups, er, kn, frozen, recipe)}}


def main():
    p = argparse.ArgumentParser()
    for key in ("base", "protocol", "output", "sph-config"):
        p.add_argument(f"--{key}", type=Path, required=True)
    a = p.parse_args()
    protocol = read(a.protocol)
    data, policy = load(a.base, a.sph_config)
    result = {name: evaluate(*data[name], protocol["selective"]) for name in protocol["selective"]["cohorts"]}
    write_new(a.output, {"job": os.environ.get("SLURM_JOB_ID"), "protocol_sha256": digest(a.protocol),
                         "design": protocol["design"], "sealed_receipts": SEALED, "cutoffs": policy["cutoffs"],
                         "rowwise_routing_reproduced": True, "individual_data_exported": False, "cohorts": result})


if __name__ == "__main__":
    main()
