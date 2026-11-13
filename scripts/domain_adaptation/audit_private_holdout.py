"""Recompute the held-out point estimates and primary CIs inside CEDIA."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
from pathlib import Path

import numpy as np
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "docs/domain_adaptation/MULTISOURCE_TRAINING_PROTOCOL.json"
MODELS = ("P6", "P8", "candidate")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def csv_rows(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def points(y, p, threshold):
    tn, fp, fn, tp = map(int, np.bincount(2 * y + (p >= threshold), minlength=4))
    pos, neg = tp + fn, tn + fp
    rank = rankdata(p, method="average")
    auc = (rank[y == 1].sum() - pos * (pos + 1) / 2) / (pos * neg)
    order = np.argsort(-p)
    scores = p[order]
    ends = np.r_[np.flatnonzero(scores[1:] != scores[:-1]), len(scores) - 1]
    positives = y[order].cumsum()[ends]
    ap = np.dot(np.diff(positives, prepend=0), positives / (ends + 1)) / pos
    bins = np.digitize(p, np.linspace(0, 1, 11)[1:-1])
    ece = np.abs(np.bincount(bins, weights=p - y, minlength=10)).sum() / len(y)
    return {"tp": tp, "tn": tn, "fp": fp, "fn": fn, "sensitivity": tp / pos, "specificity": tn / neg,
            "f1": 2 * tp / (2 * tp + fn + fp), "ppv": tp / (tp + fp) if tp + fp else None,
            "npv": tn / (tn + fn) if tn + fn else None, "auroc": auc, "auprc": ap,
            "brier": np.mean((p - y) ** 2), "ece": ece}


def macro_bootstrap(y, p, thresholds, patient, columns, config):
    keys, groups = np.unique(patient, return_inverse=True)
    cells = np.zeros((len(keys), len(MODELS), len(columns), 4), dtype=np.int64)
    for j, col in enumerate(columns):
        keep = y[:, col] >= 0
        truth = y[keep, col]
        for i, name in enumerate(MODELS):
            called = p[name][keep, col] >= thresholds[name][col]
            np.add.at(cells[:, i, j], (groups[keep], 2 * truth + called), 1)
    draws = []
    rng = np.random.default_rng(config["bootstrap_seed"])
    for _ in range(config["bootstrap_replicates"]):
        counts = np.bincount(rng.integers(len(keys), size=len(keys)), minlength=len(keys))
        tn, fp, fn, tp = np.einsum("g,gmec->mec", counts, cells).transpose(2, 0, 1)
        if np.any(tn + fp == 0) or np.any(tp + fn == 0):
            continue
        draws.append(np.divide(2 * tp, 2 * tp + fp + fn, out=np.zeros_like(tp, dtype=float),
                               where=2 * tp + fp + fn != 0).mean(axis=1))
    samples = np.asarray(draws)
    limits = np.quantile(samples, [.025, .975], axis=0)
    paired = np.quantile(samples[:, 2, None] - samples[:, :2], [.025, .975], axis=0)
    return limits, paired, len(samples)


def run(scored, aggregate, output):
    config = json.loads(PROTOCOL.read_bytes())
    evidence = aggregate / "WITHIN_CODE_EVALUATION_RECEIPT.json"
    seal = json.loads(evidence.read_bytes())
    private = scored / "private_test_predictions.npz"
    if (sha(private) != seal["private_prediction_sha256"] or sha(PROTOCOL) != seal["protocol_sha256"]
            or any(sha(aggregate / name) != h for name, h in seal["aggregates"].items())):
        raise ValueError("audit inputs do not match the sealed original run")
    with np.load(private, allow_pickle=False) as data:
        y, patient, length = data["labels"].astype(int), data["patients"], data["durations"]
        p = {model: data[model] for model in MODELS}
    thresholds = seal["operating_thresholds"]
    scopes = {"all": np.ones(len(y), bool), "short_7p335": length == 917, "long_10": length == 1250}
    endpoints = list(config["endpoints"])
    point_error, interval_error, comparisons, ci_comparisons = 0., 0., 0, 0
    for row in csv_rows(aggregate / "EXTERNAL_PER_CLASS_RESULTS.csv"):
        col = endpoints.index(row["endpoint"])
        subset = scopes[row["duration"]]
        supported = min(len(set(patient[subset & (y[:, col] == c)])) for c in (0, 1)) >= (
            config["calibration"]["support_min_positive_and_negative_patients"])
        if supported != (row["estimable"] == "True"):
            raise ValueError("patient support decision differs")
        if not supported:
            continue
        keep = subset & (y[:, col] >= 0)
        metrics = points(y[keep, col], p[row["model"]][keep, col], thresholds[row["model"]][col])
        for name, value in metrics.items():
            if value is None:
                if row[name]:
                    raise ValueError("undefined point estimate differs")
            else:
                point_error = max(point_error, abs(float(value) - float(row[name])))
            comparisons += 1
    macro_rows = csv_rows(aggregate / "EXTERNAL_MACRO_F1_COMPARISON.csv")
    for scope, keep in scopes.items():
        rows = {r["model"]: r for r in macro_rows if r["duration"] == scope}
        if not rows or not rows["candidate"]["endpoints"]:
            continue
        columns = [endpoints.index(e) for e in rows["candidate"]["endpoints"].split("|")]
        ci, paired, count = macro_bootstrap(y[keep], {m: a[keep] for m, a in p.items()},
                                          thresholds, patient[keep], columns, config["calibration"])
        for i, model in enumerate(MODELS):
            row = rows[model]
            interval_error = max(interval_error, abs(ci[0, i] - float(row["ci_low"])),
                                 abs(ci[1, i] - float(row["ci_high"])))
            ci_comparisons += 2
            if i < 2:
                if count != int(row["paired_replicates"]):
                    raise ValueError("patient bootstrap accepted count differs")
                interval_error = max(interval_error, abs(paired[0, i] - float(row["paired_ci_low"])),
                                     abs(paired[1, i] - float(row["paired_ci_high"])))
                ci_comparisons += 2
    if point_error > 1e-12 or interval_error > 1e-12:
        raise ValueError(f"independent recomputation mismatch: points={point_error}, intervals={interval_error}")
    result = {"scope": "PRIVATE_SCORES_READBACK_WITHIN_CODE_ONLY", "ecgs": len(y), "patients": len(set(patient)),
              "score_sha256": sha(private), "aggregate_receipt_sha256": sha(evidence), "point_comparisons": comparisons,
              "macro_ci_endpoint_comparisons": ci_comparisons, "max_abs_point_difference": point_error,
              "max_abs_macro_ci_difference": interval_error, "status": "PASS", "slurm_job": os.getenv("SLURM_JOB_ID"),
              "code_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()}
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("scored", "aggregate", "output"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    run(args.scored, args.aggregate, args.output)
