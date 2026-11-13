"""Evaluate the sealed label-blind policy on the held SPH development partition."""
from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from pathlib import Path

import numpy as np
from compare_reviewer_baseline import PROFILES, digest
from freeze_reviewer_selective_policy import calibration_member, components, confidence, jsonl


def ratio(a, b):
    return float(a / b) if b else None


def confusion(truth, predicted, weights=None):
    return np.bincount(2 * truth + predicted, weights=weights, minlength=4)


def curve(conf, error, weights=None):
    """Threshold ties are indivisible, including in bootstrap resamples."""
    order = np.argsort(-conf, kind="stable")
    ends = np.r_[np.flatnonzero(np.diff(conf[order])), len(order) - 1]
    if not len(order):
        return [], [], None
    w = np.ones(len(conf), dtype=np.int64) if weights is None else weights
    n = np.cumsum(w[order])[ends]
    err = np.cumsum((error * w)[order])[ends]
    valid = n > 0
    if not np.any(valid):
        return [], [], None
    coverage, risk = n[valid] / n[-1], err[valid] / n[valid]
    return coverage.tolist(), risk.tolist(), float(np.dot(np.diff(np.r_[0, coverage]), risk))


def metric_summary(truth, decisions, scores, use, metric_values):
    result = metric_values(truth, decisions, scores, use.astype(np.int64), 10)
    if not use.any():
        return {k: None for k in result}
    return result


def profile_stats(rows, names, metric_values, design):
    conf = np.array([r["confidence"] for r in rows])
    accepted = np.array([r["route"] == "accepted" for r in rows])
    scored = np.array([r["route"] != "not_scored" for r in rows])
    truth = np.array([r["reference"] for r in rows], dtype=np.int8)
    decision = np.array([r["decision"] for r in rows], dtype=np.int8)
    scores = np.array([r["scores"] for r in rows])
    error = (truth != decision).mean(axis=1)
    coverage, risk, aurc = curve(conf[scored], error[scored])
    # Publish a fixed coverage grid, not rank-by-rank outcomes.
    grid = np.arange(1, 101) / 100
    plot = np.searchsorted(coverage, grid, side="left") if coverage else []
    routes = {"baseline": scored, "accepted": accepted, "abstained": scored & ~accepted}
    result = {"held_records": len(rows), "scored_records": int(scored.sum()),
              "accepted": int(accepted.sum()), "abstained": int(routes["abstained"].sum()),
              "technical_unscored": int((~scored).sum()),
              "abstention_all_held": ratio(routes["abstained"].sum(), len(rows)),
              "abstention_scored": ratio(routes["abstained"].sum(), scored.sum()),
              "coverage_all_held": ratio(accepted.sum(), len(rows)),
              "coverage_scored": ratio(accepted.sum(), scored.sum()),
              "selective_risk": ratio(error[accepted].sum(), accepted.sum()),
              "aurc": aurc, "risk_coverage_curve": {
                  "requested_coverage_scored": grid.tolist() if coverage else [],
                  "attainable_coverage_scored": [coverage[i] for i in plot],
                  "risk": [risk[i] for i in plot],
              },
              "endpoints": {}}
    for i, name in enumerate(names):
        endpoint = {"held_statement_positive": int(truth[:, i].sum()), "routes": {}}
        for route, mask in routes.items():
            tn, fp, fn, tp = map(int, confusion(truth[mask, i], decision[mask, i]))
            endpoint["routes"][route] = {
                "n": int(mask.sum()), "tn": tn, "fp": fp, "fn": fn, "tp": tp,
                "metrics": metric_summary(truth[:, i], decision[:, i], scores[:, i], mask, metric_values),
            }
        result["endpoints"][name] = endpoint

    def macro(mask, w):
        out = []
        for i in range(len(names)):
            _, fp, fn, tp = confusion(truth[:, i], decision[:, i], w * mask)
            value = ratio(2 * tp, 2 * tp + fn + fp)
            if value is None:
                return None
            out.append(value)
        return float(np.mean(out))

    # Same cluster draws for baseline and selective results, no refitting.
    _, ix = np.unique([r["component"] for r in rows], return_inverse=True)
    n_clusters = int(ix.max()) + 1
    rng = np.random.default_rng(design["seed"])
    baseline_f1 = macro(scored, np.ones(len(rows)))
    accepted_f1 = macro(accepted, np.ones(len(rows)))
    result["macro_f1"] = {"baseline": baseline_f1, "accepted": accepted_f1,
                          "endpoints": list(names)}
    result["macro_binary_accuracy"] = {
        name: float(1 - error[mask].mean()) if mask.any() else None
        for name, mask in routes.items()
    }
    samples = {k: [] for k in ("abstention_all_held", "coverage_scored", "selective_risk",
                              "baseline_macro_f1", "accepted_macro_f1", "delta_macro_f1", "aurc")}
    for _ in range(design["replicates"]):
        w = np.bincount(rng.integers(n_clusters, size=n_clusters), minlength=n_clusters)[ix]
        b, a = macro(scored, w), macro(accepted, w)
        _, _, area = curve(conf[scored], error[scored], w[scored])
        values = (ratio(w[routes["abstained"]].sum(), w.sum()),
                  ratio(w[accepted].sum(), w[scored].sum()),
                  ratio(np.dot(error[accepted], w[accepted]), w[accepted].sum()), b, a,
                  a-b if a is not None and b is not None else None, area)
        for k, v in zip(samples, values, strict=True):
            if v is not None:
                samples[k].append(v)
    alpha = (1 - design["level"]) / 2
    result["fixed_policy_intervals"] = {
        k: {"bounds": np.quantile(v, [alpha, 1-alpha]).tolist() if v else None,
            "valid": len(v), "invalid": design["replicates"] - len(v)} for k, v in samples.items()
    }
    return result


def route_record(row, thresholds, cutoffs):
    """Reference-free route construction. Reference join occurs afterwards."""
    if row["status"] != "scored":
        return {p: {"route": "not_scored", "confidence": None, "original": None} for p in PROFILES}
    output = {}
    for p in PROFILES:
        original = row["profiles"][p]
        c = confidence(original["scores"], thresholds[p])
        output[p] = {"route": "accepted" if c >= cutoffs[p] else "abstained",
                     "confidence": c, "uncertainty": 1-c, "original": original}
    return output


def main():
    from titan_v45.data.sph import read_sph_dictionary, read_sph_metadata
    from titan_v45.evaluation.sph_report import _metric_values

    p = argparse.ArgumentParser(description=__doc__)
    for n in ("phase", "evaluation", "frozen-config", "source", "ledger", "receipt",
              "duplicate-index", "policy", "output", "private-ledger"):
        p.add_argument(f"--{n}", type=Path, required=True)
    p.add_argument("--expected-policy-sha256", required=True)
    a = p.parse_args()
    phase, evaluation, frozen, scoring, policy = (
        json.loads(x.read_bytes()) for x in (a.phase, a.evaluation, a.frozen_config, a.receipt, a.policy)
    )
    bas = phase["frozen_baseline"]
    if (scoring["protocol_commit"] != bas["implementation_commit"]
            or scoring["protocol_sha256"] != bas["protocol_sha256"]
            or digest(a.frozen_config) != bas["protocol_sha256"]
            or digest(a.ledger) != scoring["ledger_sha256"]
            or digest(a.duplicate_index) != scoring["private_duplicate_index_sha256"]
            or digest(a.policy) != a.expected_policy_sha256
            or policy["phase_sha256"] != digest(a.phase)
            or policy["scoring_receipt_sha256"] != digest(a.receipt)
            or policy["scoring_ledger_sha256"] != scoring["ledger_sha256"]
            or policy["duplicate_index_sha256"] != scoring["private_duplicate_index_sha256"]
            or policy["held_scores_used_for_selection"] is not False
            or policy["reference_labels_used"] is not False
            or policy["cascade_implemented"] is not False):
        raise ValueError("policy or input integrity check failed")
    for n in ("code.csv", "metadata.csv"):
        if digest(a.source/n) != scoring["source_sha256"][n]:
            raise ValueError("reference source digest mismatch")
    primary, modifier = read_sph_dictionary((a.source/"code.csv").read_text(encoding="utf-8-sig"))
    metadata = read_sph_metadata((a.source/"metadata.csv").read_text(encoding="utf-8-sig"), primary, modifier)
    groups = components(jsonl(a.duplicate_index))
    if metadata.keys() != groups.keys() or len(groups) != bas["expected_metadata_rows"]:
        raise ValueError("metadata and patient components do not reconcile")
    recipe = phase["development_selective_policy"]
    cutoffs = {k: v["accept_at_or_above"] for k, v in policy["policies"].items()}
    endpoints = {p: [e for e in frozen["endpoints"] if e["profile"] == p] for p in PROFILES}
    by_profile, seen, flow = {p: [] for p in PROFILES}, set(), Counter()
    with a.private_ledger.open("x", encoding="utf-8") as stream:
        for row in jsonl(a.ledger):
            key = row["record_id"]
            if key in seen or key not in groups:
                raise ValueError("duplicate or unexpected scoring ECG")
            seen.add(key)
            if calibration_member(groups[key], recipe["split_seed"], recipe["calibration_fraction"]):
                continue
            flow[row["status"]] += 1
            routed = route_record(row, frozen["thresholds"], cutoffs)
            for p, item in routed.items():
                original = item["original"]
                ref = [int(bool(set(e["codes"]) & metadata[key].primary_codes)) for e in endpoints[p]]
                pred = [int(e["name"] in original["labels"]) if original else 0
                        for e in endpoints[p]]
                probabilities = [original["scores"][e["name"]] if original else 0.0 for e in endpoints[p]]
                names = [e["name"] for e in endpoints[p]]
                item.update({"statement_reference": dict(zip(names, ref, strict=True)),
                             "reference_eligible": names,
                             "second_stage_prediction": None,
                             "confusion_by_endpoint": {
                                 name: ("TP" if y and d else "FN" if y else "FP" if d else "TN")
                                 if original else None for name, y, d in zip(names, ref, pred, strict=True)
                             }})
                by_profile[p].append({"component": groups[key], "route": item["route"],
                                      "confidence": item["confidence"] or 0.0, "reference": ref,
                                      "decision": pred, "scores": probabilities})
            stream.write(json.dumps({"record_id": key, "status": row["status"], "profiles": routed},
                                    allow_nan=False, separators=(",", ":"))+"\n")
    if seen != groups.keys() or sum(flow.values()) != policy["counts"]["held_records"]:
        raise ValueError("held denominator disagrees with policy freeze")
    report = {
        "scope": evaluation["population"], "job": os.environ.get("SLURM_JOB_ID"),
        "policy_sha256": a.expected_policy_sha256, "evaluation_protocol_sha256": digest(a.evaluation),
        "private_route_ledger_sha256": digest(a.private_ledger), "held_flow": dict(flow),
        "reference_semantics": evaluation["compatible_endpoints"], "risk_definition": evaluation["risk"],
        "bootstrap": evaluation["intervals"], "cascade_implemented": False,
        "reference_labels_used_for_routing": False,
        "profiles": {p: profile_stats(rows, [e["name"] for e in endpoints[p]],
                                      _metric_values, evaluation["intervals"])
                     for p, rows in by_profile.items()},
    }
    with a.output.open("x", encoding="utf-8") as f:
        json.dump(report, f, allow_nan=False, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
