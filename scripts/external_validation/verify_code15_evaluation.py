"""Independently verify CODE result point estimates from private CEDIA predictions."""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np
from code15_io import PROTOCOL, digest
from scipy.stats import rankdata


def independent_estimates(y, scores, threshold):
    pred = scores >= threshold
    pos = y == 1
    tp = int((pred & pos).sum())
    fp = int((pred & ~pos).sum())
    fn = int((~pred & pos).sum())
    tn = int((~pred & ~pos).sum())
    p, n = tp + fn, tn + fp
    ranks = rankdata(scores, method="average")
    auroc = (ranks[pos].sum() - p * (p + 1) / 2) / (p * n)
    distinct = np.unique(scores)
    bins = np.searchsorted(distinct, scores)
    pos_by_score = np.bincount(bins[pos], minlength=len(distinct))[::-1]
    all_by_score = np.bincount(bins, minlength=len(distinct))[::-1]
    precision = np.cumsum(pos_by_score) / np.cumsum(all_by_score)
    return {"tp": tp, "tn": tn, "fp": fp, "fn": fn, "sensitivity": tp / p,
            "specificity": tn / n, "f1": 2 * tp / (2 * tp + fp + fn),
            "auroc": auroc, "auprc": np.dot(pos_by_score, precision) / p,
            "brier": np.square(y - scores).mean()}


def verify(directory: Path):
    protocol = json.loads(PROTOCOL.read_bytes())
    config = protocol["evaluation"]
    endpoints = list(protocol["reference"])
    models = {"published": "baseline", "anchored_linear_residual_v1": "candidate"}
    table = directory / "CODE15_PER_CLASS.csv"
    score_path = directory / "private_scores.npz"
    with table.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    wanted = {(p, endpoint, model) for p in config["profiles"] for endpoint in endpoints for model in models}
    keys = [(row["profile"], row["endpoint"], row["model"]) for row in rows]
    if set(keys) != wanted or len(keys) != len(wanted):
        raise ValueError("missing or duplicate metric keys")
    with np.load(score_path, allow_pickle=False) as payload:
        labels, patients, exams = (payload[name] for name in ("labels", "patients", "exams"))
        if (labels.shape != (len(patients), len(endpoints)) or len(exams) != len(patients)
                or len(set(exams)) != len(exams) or not np.isin(labels, [-1, 0, 1]).all()):
            raise ValueError("private predictions have inconsistent exam/label alignment")
        thresholds = {}
        for row in rows:
            profile, endpoint = row["profile"], row["endpoint"]
            col = endpoints.index(endpoint)
            mask = labels[:, col] >= 0
            y = labels[mask, col]
            groups = patients[mask]
            probabilities = payload[f"{models[row['model']]}_{profile}"]
            if (probabilities.shape != labels.shape or not np.isfinite(probabilities).all()
                    or np.any((probabilities < 0) | (probabilities > 1))):
                raise ValueError("invalid private probabilities")
            threshold = float(row["threshold"])
            if not 0 <= threshold <= 1 or thresholds.setdefault((profile, endpoint), threshold) != threshold:
                raise ValueError("candidate threshold is not identical to baseline")
            supports = [int((y == target).sum()) for target in (0, 1)]
            patient_supports = [len(np.unique(groups[y == target])) for target in (0, 1)]
            expected_support = [len(y), *supports, *patient_supports]
            actual_support = [int(row[name]) for name in ("n_ecg_with_reference", "n_negative_ecg",
                              "n_positive_ecg", "n_negative_patients", "n_positive_patients")]
            if expected_support != actual_support:
                raise ValueError("reported denominators differ from aligned labels")
            estimable = min(patient_supports) >= config["minimum_distinct_positive_and_negative_patients"]
            if row["estimable"] != str(estimable):
                raise ValueError("reference support criterion not respected")
            if not estimable:
                if any(row[name] for name in ("f1", "tp", "tn", "fp", "fn", "auroc", "auprc", "brier")):
                    raise ValueError("unsupported row has reported metrics")
                continue
            expected = independent_estimates(y, probabilities[mask, col], threshold)
            for name, value in expected.items():
                if not math.isclose(float(row[name]), value, abs_tol=1e-8, rel_tol=1e-8):
                    raise ValueError(f"independent point estimate mismatch: {profile}/{endpoint}/{name}")
                if name in {"tp", "tn", "fp", "fn"}:
                    continue
                valid = int(row[name + "_valid_replicates"])
                if not 0 < valid <= config["bootstrap_replicates"]:
                    raise ValueError("invalid bootstrap replicate count")
                low, high = (float(row[name + "_ci_" + bound]) for bound in ("low", "high"))
                if not 0 <= low <= high <= 1:
                    raise ValueError("invalid reported interval")
    result = {"status": "PASS", "metric_rows_verified": len(rows),
              "aggregate_csv_sha256": digest(table), "private_scores_sha256": digest(score_path),
              "scope": "Independent point estimates; bootstrap interval structural validation."}
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evaluation_dir", type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.evaluation_dir), sort_keys=True))
