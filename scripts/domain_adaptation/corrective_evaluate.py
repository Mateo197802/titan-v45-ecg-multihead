"""Calibrate sealed fits, freeze a finalist, and reduce matched development scores."""
from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev

import numpy as np
import torch
from corrective_audit import PROTOCOL, cfg
from recovery_calibration import (
    baseline_metrics,
    choose_cut,
    csv_write,
    fit_map,
    guard_limits,
    load_score,
    operating_frontier,
    transform,
)
from recovery_inputs import SOURCES, config, parent_model, score_model
from recovery_training import RecoveryNet, get_code, get_other
from train_duration_aware import digest, write_json

from titan_v45.evaluation.revision_report import binary_metrics

FIELDS = ("f1", "recall", "precision", "specificity", "npv", "auroc", "average_precision", "brier_score", "ece")


def measure(y, raw, prob, cut):
    m = binary_metrics(y.astype(int), raw.astype(np.float64) >= cut, prob)
    m["npv"] = m["tn"] / (m["tn"] + m["fn"]) if m["tn"] + m["fn"] else None
    return m


def calibrate(cal, p, baseline):
    cuts, maps = [], []
    for j, e in enumerate(cfg()["endpoints"]):
        y = cal["labels"][:, j]
        use = y >= 0
        cuts.append(choose_cut(y[use], p[use, j], guard_limits(baseline_metrics(cal, j, e, baseline), e))["threshold"])
        maps.append(fit_map(y[use], p[use, j], "platt"))
    return {"cuts": cuts, "maps": maps}


def aligned(new, old):
    if any(not np.array_equal(new[k], old[k]) for k in ("exams", "patients", "labels", "durations")):
        raise ValueError("comparison ECG roster differs")
    return new["p"]


def model_from(path, receipt, previous):
    if digest(path / "best.pt") != receipt["checkpoint_sha256"]:
        raise ValueError("corrective weight digest mismatch")
    state = torch.load(path / "best.pt", map_location="cpu", weights_only=True)
    if (state["arm"], state["seed"], state["protocol_sha256"]) != (
        receipt["arm"], receipt["seed"], digest(PROTOCOL)
    ):
        raise ValueError("corrective checkpoint contract mismatch")
    model = RecoveryNet(parent_model(previous, state["seed"]), "shared").cuda()
    model.load_state_dict(state["state_dict"], strict=True)
    return model


def summarize(val, p, policy, baseline, baseline_summary):
    reports, guards = [], {}
    for j, e in enumerate(cfg()["endpoints"]):
        y = val["labels"][:, j]
        use = y >= 0
        raw = p[use, j]
        cut = policy["cuts"][j]
        reports.append(measure(y[use], raw, transform(raw, policy["maps"][j]), cut))
        limits = guard_limits(baseline_metrics(val, j, e, baseline), e)
        point = operating_frontier(y[use], raw, limits, np.asarray([cut]))
        guards[e] = {"pass": bool(point["feasible"][0]), "deficit": float(point["guard_deficit"][0]), "limits": limits}
    summary = {key: mean(r[key] for r in reports) for key in ("f1", "average_precision", "brier_score", "ece")}
    c = config()["calibration"]
    calibration_ok = (summary["brier_score"] <= baseline_summary["brier_score"] + c["macro_brier_max_increase"]
                      and summary["ece"] <= baseline_summary["ece"] + c["macro_ece_max_increase"])
    return summary, guards, calibration_ok


def compare(scope, data, p, policy, bootstrap, endpoint_names):
    y, a, keys = data["labels"], data["p"], data["patients"]
    old_cut = config()["incumbent_thresholds"]
    c_prob = np.column_stack([transform(p[:, j], m) for j, m in enumerate(policy["maps"])])
    known = [j for j in range(y.shape[1]) if set(y[y[:, j] >= 0, j]) == {0, 1}]
    group_type = {"validation": "patient", "chapman": "provider_group_proxy", "cpsc": "ecg_only"}[scope]
    groups = defaultdict(list)
    for row, key in enumerate(keys):
        groups[key].append(row)
    blocks = [np.asarray(group) for group in groups.values()]
    eligible = {j for j in known if min(len(set(keys[y[:, j] == a])) for a in (0, 1))
                >= bootstrap["support_min_positive_and_negative_groups"]}

    def values(ix, columns):
        out = {}
        for j in columns:
            rows = ix[y[ix, j] >= 0]
            if len(set(y[rows, j])) < 2:
                continue
            out["A", j] = measure(y[rows, j], a[rows, j], a[rows, j], old_cut[j])
            out["C", j] = measure(y[rows, j], p[rows, j], c_prob[rows, j], policy["cuts"][j])
        return out

    points = values(np.arange(len(y)), known)
    estimates = defaultdict(list)

    def add(values, columns):
        for j in columns:
            if ("A", j) not in values:
                continue
            for field in FIELDS:
                x, z = (values[k, j][field] for k in ("A", "C"))
                for arm, value in (("A", x), ("C", z), ("C-A", z - x if x is not None and z is not None else None)):
                    if value is not None:
                        estimates[arm, j, field].append(value)
        if columns and len(values) == 2 * len(columns):
            for field in ("f1", "average_precision"):
                x, z = (mean(values[k, j][field] for j in columns) for k in ("A", "C"))
                for arm, value in (("A", x), ("C", z), ("C-A", z - x)):
                    estimates[arm, -1, field].append(value)

    add(points, known)
    observed = {k: v[0] for k, v in estimates.items()}
    estimates.clear()
    rng = np.random.default_rng(bootstrap["seed"])
    for _ in range(bootstrap["replicates"]):
        idx = np.concatenate([blocks[i] for i in rng.integers(len(blocks), size=len(blocks))])
        # Keep the macro endpoint denominator fixed; do not omit a weak endpoint from its interval.
        add(values(idx, eligible), known)
    intervals = []
    for (arm, j, field), v in observed.items():
        samples = estimates[arm, j, field]
        low, high = np.quantile(samples, [.025, .975]).tolist() if samples else (None, None)
        intervals.append({"scope": scope, "arm": arm, "endpoint": endpoint_names[j] if j >= 0 else "macro",
                          "metric": field, "value": v, "ci_low": low, "ci_high": high,
                          "valid_replicates": len(samples), "resampling_unit": group_type})
    metrics = [{"scope": scope, "arm": arm, "endpoint": endpoint_names[j],
                **{k: row[k] for k in ("rows", "positive_support", "negative_support", "tp", "tn", "fp", "fn", *FIELDS)}}
               for (arm, j), row in points.items()]
    return metrics, intervals


def run(previous, archived, audit, fits, output):
    c = cfg()
    if not json.loads(audit.read_bytes())["diagnostic_pass"]:
        raise ValueError("diagnostic gate not passed")
    output.mkdir(mode=0o700, exist_ok=False)
    cal, val = (load_score(archived, name) for name in ("calibration", "validation"))
    bank = get_code(previous, "calibration", "per_lead_zscore")
    baseline = json.loads((archived / "DEVELOPMENT_SCORING_RECEIPT.json").read_bytes())
    old = {"cuts": config()["incumbent_thresholds"], "maps": [{"kind": "identity"}] * 5}
    base_summary, _, _ = summarize(val, val["p"], old, baseline,
                                  {"brier_score": float("inf"), "ece": float("inf")})
    results = []
    for path in sorted(fits.glob("*/fit.json")):
        r = json.loads(path.read_bytes())
        if (r["audit_sha256"] != digest(audit) or r["protocol_sha256"] != digest(PROTOCOL)
                or r["calibration_opened"] or r["test_opened"]):
            raise ValueError("fit provenance mismatch")
        model = model_from(path.parent, r, previous)
        calibration_score = score_model(model, bank)
        policy = calibrate(cal, aligned(calibration_score, cal), baseline)
        score_file = path.parent / "private_validation.npz"
        if digest(score_file) != r["validation_scores_sha256"]:
            raise ValueError("validation score digest mismatch")
        with np.load(score_file, allow_pickle=False) as saved:
            p = aligned(saved, val)
        metrics, guards, passes = summarize(val, p, policy, baseline, base_summary)
        results.append({**r, "policy": policy, "metrics": metrics, "class_guards": guards,
                        "calibration_guard": passes, "all_class_guards": all(g["pass"] for g in guards.values())})
    families = []
    for arm in c["arms"]:
        family = [r for r in results if r["arm"] == arm]
        if {r["seed"] for r in family} == set(c["seeds"]):
            f1 = [r["epoch"]["selection"][2] for r in family]
            families.append((sum(r["all_class_guards"] for r in family), mean(f1),
                             mean(r["metrics"]["average_precision"] for r in family), arm, stdev(f1)))
    if not families:
        raise ValueError("no three-seed corrective family completed")
    family = max(families)
    selected = sorted([r for r in results if r["arm"] == family[3]],
                      key=lambda r: (r["epoch"]["selection"][2], r["seed"]))[1]
    seal = {"protocol_sha256": digest(PROTOCOL), "audit_sha256": digest(audit), "selected": selected,
            "families": families, "slurm_job": os.getenv("SLURM_JOB_ID"), "test_opened": False}
    write_json(output / "CORRECTIVE_SELECTION.json", seal)
    write_json(output / "CORRECTIVE_FITS.json", results)
    model = model_from(fits / f"{selected['arm']}-{selected['seed']}", selected, previous)
    all_metrics, all_ci, private_hashes = [], [], {}
    for scope in ("validation", *SOURCES):
        data = val if scope == "validation" else load_score(archived, scope)
        source = (get_code(previous, "validation", "per_lead_zscore") if scope == "validation" else
                  get_other(previous, *SOURCES[scope], "per_lead_zscore"))
        p = aligned(score_model(model, source), data)
        path = output / f"private_{scope}.npz"
        np.savez_compressed(path, labels=data["labels"], patients=data["patients"], exams=data["exams"],
                            incumbent=data["p"], candidate=p)
        private_hashes[path.name] = digest(path)
        rows, intervals = compare(scope, data, p, selected["policy"], c["paired_bootstrap"], c["endpoints"])
        all_metrics.extend(rows)
        all_ci.extend(intervals)
    csv_write(output / "CORRECTIVE_METRICS.csv", all_metrics)
    csv_write(output / "CORRECTIVE_PAIRED_INTERVALS.csv", all_ci)
    macro = {(r["scope"], r["arm"], r["metric"]): r for r in all_ci if r["endpoint"] == "macro"}
    gain = macro["validation", "C-A", "f1"]
    guards = {"target_f1": selected["metrics"]["f1"] >= .70, "paired_gain": (gain["ci_low"] or -1) > 0,
              "all_class_guards": selected["all_class_guards"], "all_three_seeds_class_guards": family[0] == 3,
              "calibration": selected["calibration_guard"],
              "source_guard": all(macro[s, "C-A", "f1"]["value"] >= -.03 for s in SOURCES)}
    names = ("CORRECTIVE_SELECTION.json", "CORRECTIVE_FITS.json", "CORRECTIVE_METRICS.csv", "CORRECTIVE_PAIRED_INTERVALS.csv")
    write_json(output / "CORRECTIVE_DECISION.json", {
        "protocol_sha256": digest(PROTOCOL), "slurm_job": os.getenv("SLURM_JOB_ID"), "guards": guards,
        "development_success": all(guards.values()), "independent_generalization": "NOT_EVALUATED",
        "promotion": "NOT_AUTHORIZED", "test_opened": False, "private_score_sha256": private_hashes,
        "public_sha256": {name: digest(output / name) for name in names}})
    print(json.dumps(guards), flush=True)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    for arg in ("previous", "archived", "audit", "fits", "output"):
        cli.add_argument(arg, type=Path)
    run(**vars(cli.parse_args()))
