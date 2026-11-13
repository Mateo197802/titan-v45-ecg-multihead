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
    scores = scores.astype(np.float64)
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
            "ppv": tp / (tp + fp) if tp + fp else None,
            "npv": tn / (tn + fn) if tn + fn else None,
            "ece": sum(row["n_ecg"] * abs(row["observed_fraction"] - row["mean_score"])
                       for row in calibration_bins(y, scores) if row["n_ecg"]) / len(y),
            "auroc": auroc, "auprc": np.dot(pos_by_score, precision) / p,
            "brier": np.square(y - scores).mean()}


def verify(directory: Path, *, replay=None, decisions=None):
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
            expected_support = [len(y), len(np.unique(groups)), *supports, *patient_supports]
            actual_support = [int(row[name]) for name in ("n_ecg_with_reference", "n_patients_with_reference", "n_negative_ecg",
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
                if value is None:
                    if row[name]:
                        raise ValueError("reported point estimate has zero denominator")
                    continue
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
        if replay is not None:
            keyed = dict(zip(keys, rows, strict=True))
            for profile in config["profiles"]:
                replay_rows, replay_decision = replay(
                    labels, payload["baseline_" + profile], payload["candidate_" + profile],
                    patients, np.asarray([thresholds[profile, name] for name in endpoints]), endpoints, config,
                )
                for row in replay_rows:
                    original = keyed[profile, row["endpoint"], row["model"]]
                    for field, value in row.items():
                        serialized = "" if value is None else str(value)
                        if serialized != original[field]:
                            raise ValueError(f"bootstrap replay disagrees on {profile}/{row['endpoint']}/{field}")
                if decisions is not None and any(value != decisions[profile].get(key)
                                                 for key, value in replay_decision.items()):
                    raise ValueError(f"replayed paired decision disagrees on {profile}")
    result = {"status": "PASS", "metric_rows_verified": len(rows),
              "aggregate_csv_sha256": digest(table), "private_scores_sha256": digest(score_path),
              "patient_bootstrap_replayed": replay is not None,
              "scope": "Independent point estimates; optional exact patient-bootstrap replay."}
    return result


def calibration_bins(y, scores):
    edges = np.linspace(0.0, 1.0, 11)
    bins = np.digitize(scores, edges[1:-1])
    for i in range(10):
        keep = bins == i
        n = int(keep.sum())
        yield {"bin": i, "lower": edges[i], "upper": edges[i + 1], "n_ecg": n,
               "mean_score": float(scores[keep].mean()) if n else None,
               "observed_fraction": float(y[keep].mean()) if n else None}


def write_aggregate_views(directory, decisions, n_ecg, n_patients, complete, endpoints):
    with (directory / "CODE15_PER_CLASS.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    scope = "FULL_FROZEN_SAMPLE" if complete else "FIRST_ARCHIVE_ONLY_NO_PROMOTION"
    counts_fields = ("profile", "endpoint", "model", "estimable", "n_ecg_with_reference",
                     "n_patients_with_reference", "n_positive_ecg", "n_negative_ecg", "tp", "tn", "fp", "fn")
    macro = []
    for profile, result in decisions.items():
        for i, model in enumerate(("published", "anchored_linear_residual_v1")):
            ci = result.get("macro_f1_ci95", [[None, None], [None, None]])[i]
            macro.append({"profile": profile, "model": model, "n_ecg": n_ecg, "n_patients": n_patients,
                          "endpoints": "|".join(result["macro_f1_classes"]),
                          "macro_f1": result.get("macro_f1", [None, None])[i], "ci_low": ci[0], "ci_high": ci[1],
                          "delta": result.get("macro_f1_delta") if i else None,
                          "paired_ci_low": result.get("delta_ci95", [None, None])[0] if i else None,
                          "paired_ci_high": result.get("delta_ci95", [None, None])[1] if i else None,
                          "empty_set_count": result["empty_sets"][i],
                          "decision": result["decision"] if i else "REFERENCE"})
    views = {
        "EXTERNAL_CODE15_RESULTS.csv": rows,
        "EXTERNAL_PER_CLASS_CONFUSION.csv": [{k: row[k] for k in counts_fields} for row in rows],
        "EXTERNAL_CODE15_MACRO.csv": macro,
    }
    curves = []
    with np.load(directory / "private_scores.npz", allow_pickle=False) as scores:
        labels = scores["labels"]
        for row in rows:
            if row["estimable"] != "True":
                continue
            column = endpoints.index(row["endpoint"])
            eligible = labels[:, column] >= 0
            kind = "baseline" if row["model"] == "published" else "candidate"
            p = scores[f"{kind}_{row['profile']}"][eligible, column].astype(np.float64)
            for item in calibration_bins(labels[eligible, column], p):
                curves.append({**{key: row[key] for key in ("profile", "model", "endpoint")}, **item})
    if curves:
        views["EXTERNAL_CODE15_CALIBRATION.csv"] = curves
    hashes = {}
    for name, entries in views.items():
        path = directory / name
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=["scope", *entries[0]], lineterminator="\n")
            writer.writeheader()
            writer.writerows({"scope": scope, **item} for item in entries)
        hashes[name] = digest(path)
    return hashes


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evaluation_dir", type=Path)
    parser.add_argument("--replay-bootstrap", action="store_true")
    args = parser.parse_args()
    replay = None
    decisions = None
    if args.replay_bootstrap:
        from evaluate_code15 import paired_metrics

        replay = paired_metrics
        decisions = json.loads((args.evaluation_dir / "code15_evaluation_receipt.json").read_bytes())["promotion"]
    print(json.dumps(verify(args.evaluation_dir, replay=replay, decisions=decisions), sort_keys=True))
