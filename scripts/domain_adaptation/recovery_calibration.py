"""Grouped calibration and classwise development operating-frontier analysis."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path

import numpy as np
from recovery_inputs import RECOVERY, config
from scipy.optimize import minimize
from scipy.special import expit, logit
from train_duration_aware import digest, write_json

from titan_v45.evaluation.revision_report import binary_metrics


def csv_write(path, rows):
    rows = list(rows)
    if not rows:
        raise ValueError(f"empty output: {path.name}")
    with path.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def load_score(folder, name):
    receipt = json.loads((folder / "DEVELOPMENT_SCORING_RECEIPT.json").read_bytes())
    path = folder / f"private_{name}.npz"
    if receipt["protocol_sha256"] != digest(RECOVERY) or digest(path) != receipt["private_artifact_sha256"][path.name]:
        raise ValueError("development score custody check failed")
    with np.load(path, allow_pickle=False) as values:
        return dict(values)


def grouped_folds(patient):
    group = sorted(set(patient), key=lambda p: hashlib.sha256(f"recovery-cal-v1|{p}".encode()).digest())
    lookup = {p: i % 3 for i, p in enumerate(group)}
    return np.asarray([lookup[p] for p in patient])


def pava(y, p):
    x, group = np.unique(p, return_inverse=True)
    n = np.bincount(group)
    total = np.bincount(group, weights=y)
    blocks = []
    for i in range(len(x)):
        blocks.append((i, i + 1, float(total[i]), int(n[i])))
        while len(blocks) > 1 and blocks[-2][2] / blocks[-2][3] > blocks[-1][2] / blocks[-1][3]:
            a, b = blocks[-2:]
            blocks[-2:] = [(a[0], b[1], a[2] + b[2], a[3] + b[3])]
    values = np.empty(len(x))
    for a, b, total, count in blocks:
        values[a:b] = total / count
    return {"kind": "isotonic", "x": x.tolist(), "y": values.tolist()}


def fit_map(y, p, method):
    if method == "identity":
        return {"kind": "identity"}
    if method == "isotonic" and min(int(y.sum()), int(len(y) - y.sum())) >= 35:
        return pava(y, p)
    method = "platt" if method == "isotonic" else method
    x = logit(np.clip(p, 1e-6, 1 - 1e-6))

    def objective(beta):
        z = beta[0] * x + (beta[1] if len(beta) > 1 else 0)
        penalty = 1e-4 * ((beta[0] - 1) ** 2 + (beta[1] ** 2 if len(beta) > 1 else 0))
        return float(np.mean(np.logaddexp(0, z) - y * z) + penalty)

    start, bounds = ([1], [(.05, 10)]) if method == "temperature" else ([1, 0], [(.05, 10), (-12, 12)])
    result = minimize(objective, start, bounds=bounds, method="L-BFGS-B")
    if not result.success:
        raise ValueError(f"calibration optimizer failed for {method}")
    return {"kind": method, "slope": float(result.x[0]), "intercept": float(result.x[1]) if len(start) == 2 else 0.}


def transform(p, mapping):
    if mapping["kind"] == "identity":
        return p
    if mapping["kind"] == "isotonic":
        return np.interp(p, mapping["x"], mapping["y"])
    return expit(mapping["slope"] * logit(np.clip(p, 1e-6, 1 - 1e-6)) + mapping["intercept"])


def guard_limits(base, endpoint):
    c = config()["calibration"]
    drop = c["max_guard_drop"]
    if endpoint == "AFIB":
        return {"sensitivity_min": max(base[k]["recall"] for k in ("P6", "P8")) - drop}
    if endpoint == "1AVB":
        return {"ppv_min": max(base[k]["precision"] or 0 for k in ("P6", "P8")) - drop,
                "sensitivity_min": base["A"]["recall"] - drop}
    if endpoint == "SB":
        return {"sensitivity_min": max(c["sb_min_sensitivity"], base["A"]["recall"]),
                "ppv_min": c["sb_min_ppv"], "fp_max": c["sb_max_fp_ratio_incumbent"] * base["A"]["fp"]}
    return {"sensitivity_min": base["A"]["recall"] - drop, "ppv_min": (base["A"]["precision"] or 0) - drop}


def operating_frontier(y, p, limits, grid=None):
    y, p = np.asarray(y, dtype=int), np.asarray(p, dtype=float)
    order = np.argsort(p, kind="stable")
    ordered, truth = p[order], y[order]
    if grid is None:
        unique = np.unique(p)
        grid = np.r_[unique[0], (unique[1:] + unique[:-1]) / 2, np.nextafter(unique[-1], np.inf)]
    tn_idx = np.searchsorted(ordered, grid, side="left")
    pos = int(y.sum())
    neg = len(y) - pos
    fn = np.r_[0, np.cumsum(truth)][tn_idx]
    tn = tn_idx - fn
    tp, fp = pos - fn, neg - tn
    ppv = np.divide(tp, tp + fp, out=np.zeros(len(grid)), where=tp + fp > 0)
    sensitivity = tp / max(pos, 1)
    f1 = np.divide(2 * tp, 2 * tp + fp + fn, out=np.zeros(len(grid)), where=2 * tp + fp + fn > 0)
    deficit = (np.maximum(0., limits.get("ppv_min", 0) - ppv)
               + np.maximum(0., limits.get("sensitivity_min", 0) - sensitivity)
               + np.maximum(0., fp - limits.get("fp_max", np.inf)) / max(neg, 1))
    return {"threshold": grid, "tp": tp, "tn": tn, "fp": fp, "fn": fn, "ppv": ppv, "sensitivity": sensitivity,
            "specificity": tn / max(neg, 1), "f1": f1, "guard_deficit": deficit, "feasible": deficit <= 1e-12}


def choose_cut(y, p, limits):
    frontier = operating_frontier(y, p, limits)
    deficit = np.where(frontier["feasible"], 0, frontier["guard_deficit"])
    i = np.lexsort((-frontier["specificity"], -frontier["ppv"], -frontier["f1"], deficit))[0]
    return {k: a[i].item() for k, a in frontier.items()}


def bm(y, p, cut):
    return binary_metrics(y.astype(int), p.astype(np.float64) >= cut, p)


def methods(cal, probs):
    fold = grouped_folds(cal["patients"])
    methods = config()["calibration"]["methods"]
    scores, predictions = [], {}
    for method in methods:
        predictions[method] = np.empty_like(probs, dtype=float)
        for j in range(probs.shape[1]):
            actual = eligible_method(method, cal["labels"][:, j], fold)
            for k in range(3):
                train = (fold != k) & (cal["labels"][:, j] >= 0)
                valid = fold == k
                if len(set(cal["labels"][train, j])) != 2:
                    raise ValueError("calibration fitting fold lacks support")
                m = fit_map(cal["labels"][train, j], probs[train, j], actual)
                predictions[method][valid, j] = transform(probs[valid, j], m)
        m = [bm(cal["labels"][:, j], predictions[method][:, j], .5) for j in range(probs.shape[1])]
        scores.append({"method": method, "macro_brier": float(np.mean([r["brier_score"] for r in m])),
                       "macro_ece": float(np.mean([r["ece"] for r in m]))})
    lowest = min(row["macro_brier"] for row in scores)
    best = next(row["method"] for row in scores if row["macro_brier"] <= lowest + .0002)
    return best, scores, predictions


def eligible_method(method, labels, fold):
    if method == "isotonic" and any(
        min(np.sum(labels[fold != k] == target) for target in (0, 1)) < 35 for k in range(3)
    ):
        return "platt"
    return method


def baseline_metrics(data, j, endpoint, receipt):
    keep = data["labels"][:, j] >= 0
    y = data["labels"][keep, j]
    base = {"A": bm(y, data["p"][keep, j], config()["incumbent_thresholds"][j])}
    for name in ("P6", "P8"):
        base[name] = bm(y, data[name][keep, j], receipt["published_thresholds"][name][endpoint])
    return base


def audit_rows(data, probs, thresholds, scope, arm):
    cfg = config()
    known = data["rr"][:, 3] > 0
    hr = data["rr"][:, 0]
    partitions = {
        "all": np.ones(len(hr), dtype=bool), "short": data["durations"] == 917, "long": data["durations"] == 1250,
        "qrs_confident": known, "qrs_unavailable": ~known,
        "hr_below_60": known & (hr < 60), "hr_60_to_100": known & (hr >= 60) & (hr <= 100),
        "hr_above_100": known & (hr > 100), "rr_cv_at_least_0_12": known & (data["rr"][:, 1] >= .12),
        "rr_cv_below_0_12": known & (data["rr"][:, 1] < .12),
        "higher_high_frequency_proxy": data["noise_proxy"] >= .2, "lower_high_frequency_proxy": data["noise_proxy"] < .2,
    }
    for j, endpoint in enumerate(cfg["endpoints"]):
        for group, mask in partitions.items():
            valid = mask & (data["labels"][:, j] >= 0)
            y, p = data["labels"][valid, j], probs[valid, j]
            if valid.sum() < cfg["diagnosis"]["min_aggregate_stratum_ecgs"]:
                continue
            r = bm(y, p, thresholds[j])
            neg, pos = (float(np.mean(p[y == target])) if np.sum(y == target) >= 10 else None for target in (0, 1))
            yield {"scope": scope, "arm": arm, "endpoint": endpoint, "stratum": group,
                   "ecgs": int(valid.sum()), "patients": len(set(data["patients"][valid])) if scope != "cpsc" else None,
                   "positive_support": r["positive_support"], "negative_support": r["negative_support"],
                   **{k: r[k] for k in ("tp", "tn", "fp", "fn", "recall", "precision", "f1", "average_precision", "auroc")},
                   "positive_mean_score": pos, "negative_mean_score": neg,
                   "positive_mean_margin": pos - thresholds[j] if pos is not None else None,
                   "negative_mean_margin": neg - thresholds[j] if neg is not None else None,
                   "pr_interval_status": "NOT_MEASURED"}


def candidate_probs(folder, scope, data):
    file = folder / f"private_{scope}.npz"
    receipt = json.loads((folder / "MODEL_RECOVERY_FIT_RECEIPT.json").read_bytes())
    if digest(file) != receipt["private_score_sha256"][file.name]:
        raise ValueError("candidate score custody failure")
    with np.load(file, allow_pickle=False) as z:
        if any(not np.array_equal(z[k], data[k]) for k in ("exams", "labels", "patients")):
            raise ValueError("candidate and comparator rows differ")
        return z["p"]


def run(diagnostics, out, candidate=None):
    cfg = config()
    receipt = json.loads((diagnostics / "DEVELOPMENT_SCORING_RECEIPT.json").read_bytes())
    cal, val = (load_score(diagnostics, scope) for scope in ("calibration", "validation"))
    cohorts = {"calibration": cal, "validation": val,
               **{scope: load_score(diagnostics, scope) for scope in ("chapman", "cpsc")}}
    out.mkdir(mode=0o700, exist_ok=False)
    candidates = {"B": None, **({"C": candidate} if candidate else {})}
    ablations, frontiers, reports, domains, policies, validation_guards = [], [], [], [], {}, {}
    old_thresholds = cfg["incumbent_thresholds"]
    for scope, data in cohorts.items():
        reports.extend(audit_rows(data, data["p"], old_thresholds, scope, "A"))
    for arm, folder in candidates.items():
        training_sources = (json.loads((folder / "MODEL_RECOVERY_FIT_RECEIPT.json").read_bytes())["training_sources"]
                            if folder else ())
        probs = {scope: candidate_probs(folder, scope, data) if folder else data["p"]
                 for scope, data in cohorts.items() if scope != "cpsc" or "cpsc" not in training_sources}
        best, choices, _ = methods(cal, probs["calibration"])
        ablations.extend({"arm": arm, "scope": "grouped_oof_calibration", "chosen": row["method"] == best, **row}
                         for row in choices)
        cuts, maps = [], []
        for j, endpoint in enumerate(cfg["endpoints"]):
            labels = cal["labels"][:, j]
            p = probs["calibration"][:, j]
            limits = guard_limits(baseline_metrics(cal, j, endpoint, receipt), endpoint)
            cut = choose_cut(labels, p, limits)
            cuts.append(cut["threshold"])
            maps.append(fit_map(labels, p, eligible_method(best, labels, grouped_folds(cal["patients"]))))
            for scope, data in (("calibration", cal), ("validation", val)):
                public = operating_frontier(data["labels"][:, j], probs[scope][:, j],
                                            guard_limits(baseline_metrics(data, j, endpoint, receipt), endpoint),
                                            grid=np.linspace(0, 1, 101))
                frontiers.extend({"arm": arm, "scope": scope, "endpoint": endpoint,
                                  **{key: arr[k].item() for key, arr in public.items()}} for k in range(101))
            policies[f"{arm}_{endpoint}"] = {"limits": limits, "calibration": cut,
                                               "mapping": maps[-1] if maps[-1]["kind"] != "isotonic" else {"kind": "isotonic"}}
        if best == "isotonic":
            private_map = out / f"private_{arm}_calibrator.json"
            write_json(private_map, maps)
        for scope, data in cohorts.items():
            if scope not in probs:
                continue
            p = probs[scope]
            for j, endpoint in enumerate(cfg["endpoints"]):
                keep = data["labels"][:, j] >= 0
                if not np.any(keep):
                    continue
                y = data["labels"][keep, j]
                raw = p[keep, j]
                calibrated = transform(raw, maps[j])
                r = binary_metrics(y.astype(int), raw.astype(np.float64) >= cuts[j], calibrated)
                domains.append({"arm": arm, "scope": scope, "endpoint": endpoint, "source_claim": "development_only",
                                "raw_auprc": bm(y, raw, cuts[j])["average_precision"],
                                **{k: r[k] for k in ("rows", "positive_support", "negative_support", "recall", "precision",
                                                     "f1", "tp", "fp", "tn", "fn", "average_precision", "auroc",
                                                     "brier_score", "ece")}})
                if scope == "validation":
                    limits = guard_limits(baseline_metrics(val, j, endpoint, receipt), endpoint)
                    row = operating_frontier(y, raw, limits, grid=np.asarray([cuts[j]]))
                    validation_guards[f"{arm}_{endpoint}"] = {"limits": limits, "feasible": bool(row["feasible"][0]),
                                                               "guard_deficit": float(row["guard_deficit"][0])}
            reports.extend(audit_rows(data, p, cuts, scope, arm))
    for scope, data in cohorts.items():
        for j, endpoint in enumerate(cfg["endpoints"]):
            keep = data["labels"][:, j] >= 0
            if not np.any(keep):
                continue
            r = bm(data["labels"][keep, j], data["p"][keep, j], old_thresholds[j])
            domains.append({"arm": "A", "scope": scope, "endpoint": endpoint, "source_claim": "development_only",
                            "raw_auprc": r["average_precision"], **{k: r[k] for k in (
                                "rows", "positive_support", "negative_support", "recall", "precision", "f1", "tp", "fp",
                                "tn", "fn", "average_precision", "auroc", "brier_score", "ece")}})
    csv_write(out / "CLASSWISE_FAILURE_DIAGNOSIS.csv", reports)
    csv_write(out / "CLASSWISE_FALSE_POSITIVE_FALSE_NEGATIVE_AUDIT.csv",
              [row for row in reports if row["stratum"] == "all"])
    csv_write(out / "THRESHOLD_SENSITIVITY_PRECISION_FRONTIERS.csv", frontiers)
    csv_write(out / "CALIBRATION_ABLATIONS.csv", ablations)
    csv_write(out / "DOMAIN_GENERALIZATION_MATRIX.csv", domains)
    summary = {}
    for arm in ("A", *candidates):
        rows = [r for r in domains if r["arm"] == arm and r["scope"] == "validation"]
        summary[arm] = {f"macro_{key}": float(np.mean([r[key] for r in rows])) for key in (
            "f1", "raw_auprc", "brier_score", "ece")}
    for arm in candidates:
        summary[arm].update({
            "macro_f1_target_met": summary[arm]["macro_f1"] >= cfg["promotion"]["development_macro_f1_target"],
            "class_guards_pass": all(validation_guards[f"{arm}_{e}"]["feasible"] for e in cfg["endpoints"]),
            "calibration_guard_pass": all(
                summary[arm][f"macro_{metric}"] - summary["A"][f"macro_{metric}"]
                <= cfg["calibration"][f"macro_{limit}_max_increase"]
                for metric, limit in (("brier_score", "brier"), ("ece", "ece"))),
        })
    incumbent_feasible = all(policies[f"B_{e}"]["calibration"]["feasible"] for e in cfg["endpoints"])
    write_json(out / "MODEL_PROMOTION_GATES.json", {
        "stage": "development_only", "independent_confirmation": "NOT_EVALUATED", "promotion": "NOT_AUTHORIZED",
        "protocol_sha256": digest(RECOVERY), "slurm_job": os.getenv("SLURM_JOB_ID"), "policies": policies,
        "validation_guards": validation_guards, "incumbent_calibration_all_guards_feasible": incumbent_feasible,
        "code_validation": summary, "old_test_opened": False, "frozen_promotion_rules": cfg["promotion"]})
    print(json.dumps({"incumbent_calibration_all_guards_feasible": incumbent_feasible, "code_validation": summary}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("diagnostics", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--candidate", type=Path)
    args = parser.parse_args()
    run(args.diagnostics, args.output, args.candidate)
