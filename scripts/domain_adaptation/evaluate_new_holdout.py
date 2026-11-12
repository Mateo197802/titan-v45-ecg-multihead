"""Calibrate a sealed development candidate and compare it once within CODE."""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
from evaluate_released import load_released, score_released
from train_duration_aware import (
    PROTOCOL,
    TemporalSpecialist,
    batches,
    digest,
    read_bank,
    write_json,
)

from titan_v45.evaluation.revision_report import binary_metrics
from titan_v45.models.factory import build_titan_v45_backbone

METRICS = ("sensitivity", "specificity", "ppv", "npv", "f1", "auroc", "auprc", "brier", "ece")


def measure(y, p, threshold):
    x = binary_metrics(y.astype(int), p >= threshold, p)
    return {**{name: x[name] for name in ("tp", "tn", "fp", "fn", "sensitivity", "specificity", "f1", "auroc", "ece")},
            "ppv": x["tp"] / (x["tp"] + x["fp"]) if x["tp"] + x["fp"] else None,
            "npv": x["tn"] / (x["tn"] + x["fn"]) if x["tn"] + x["fn"] else None,
            "auprc": x["average_precision"], "brier": x["brier_score"]}


def thresholds_on_calibration(y, p, endpoints):
    thresholds, summary = [], {}
    for i, endpoint in enumerate(endpoints):
        active = y[:, i] >= 0
        truth, prob = y[active, i], p[active, i]
        if len(set(truth)) != 2:
            raise ValueError("calibration lacks explicit positives or negatives")
        floor = .50 if endpoint in {"AFIB", "RBBB", "1AVB"} else 0
        options = [(level / 100, measure(truth, prob, level / 100)) for level in range(5, 96)]
        feasible = [(t, m) for t, m in options if m["sensitivity"] >= floor]
        if feasible:
            t, m = max(feasible, key=lambda x: (x[1]["f1"], x[0]))
        else:
            t, m = max(options, key=lambda x: (x[1]["sensitivity"], x[1]["f1"], x[0]))
        thresholds.append(t)
        summary[endpoint] = {"threshold": t, "floor_met": bool(feasible), "calibration_f1": m["f1"],
                             "calibration_sensitivity": m["sensitivity"]}
    return np.asarray(thresholds), summary


def candidate_scores(model, data, batch_size):
    scores, exams, patients, labels = [], [], [], []
    with torch.no_grad():
        for wave, descriptors, truth, _, ids, person in batches(data, batch_size):
            scores.append(model(torch.as_tensor(wave, device="cuda"),
                                torch.as_tensor(descriptors, device="cuda")).sigmoid().cpu().numpy())
            exams.append(ids)
            patients.append(person)
            labels.append(truth)
    return tuple(np.concatenate(x) for x in (scores, exams, patients, labels))


def intervals(y, probabilities, thresholds, patients, endpoints, cfg):
    models = list(probabilities)
    n = len(patients)
    groups = defaultdict(list)
    for i, patient in enumerate(patients):
        groups[patient].append(i)
    patients_order = sorted(groups)
    blocks = [np.asarray(groups[p]) for p in patients_order]
    supported = [min(len(set(patients[y[:, j] == k])) for k in (0, 1)) >=
                 cfg["support_min_positive_and_negative_patients"] for j in range(len(endpoints))]

    def compute(index):
        output = {}
        for j, support in enumerate(supported):
            valid = index[y[index, j] >= 0]
            if not support or len(set(y[valid, j])) != 2:
                continue
            for model in models:
                output[model, j] = measure(y[valid, j], probabilities[model][valid, j], thresholds[model][j])
        return output

    observed = compute(np.arange(n))
    estimates, deltas, macro, macro_delta = (defaultdict(list) for _ in range(4))
    rng = np.random.default_rng(cfg["bootstrap_seed"])
    for _ in range(cfg["bootstrap_replicates"]):
        values = compute(np.concatenate([blocks[i] for i in rng.integers(len(blocks), size=len(blocks))]))
        for (model, j), row in values.items():
            for metric in METRICS:
                if row[metric] is not None:
                    estimates[model, j, metric].append(row[metric])
                if model in {"P6", "P8"} and row[metric] is not None:
                    adapted = values["candidate", j][metric]
                    if adapted is not None:
                        deltas[model, j, metric].append(adapted - row[metric])
        if any(supported) and len(values) == len(models) * sum(supported):
            means = {m: float(np.mean([r["f1"] for (key, _), r in values.items() if key == m])) for m in models}
            for model, value in means.items():
                macro[model].append(value)
            for model in ("P6", "P8"):
                macro_delta[model].append(means["candidate"] - means[model])

    def ci(items):
        return np.quantile(items, [.025, .975]).tolist() if items else [None, None]

    rows, paired = [], []
    for j, endpoint in enumerate(endpoints):
        positive, negative = y[:, j] == 1, y[:, j] == 0
        counts = {"endpoint": endpoint, "positive_ecgs": int(positive.sum()), "negative_ecgs": int(negative.sum()),
                  "positive_patients": len(set(patients[positive])), "negative_patients": len(set(patients[negative])),
                  "prevalence": float(positive.sum() / max(1, (positive | negative).sum()))}
        for model in models:
            point = observed.get((model, j), dict.fromkeys(("tp", "tn", "fp", "fn", *METRICS)))
            rows.append({"model": model, "estimable": supported[j], "threshold": thresholds[model][j], **counts, **point})
            for metric in METRICS:
                values = estimates[model, j, metric]
                low, high = ci(values)
                paired.append({"baseline_or_model": model, "contrast": "point", "endpoint": endpoint, "metric": metric,
                               "value": point[metric], "ci_low": low, "ci_high": high, "replicates": len(values)})
                if model in {"P6", "P8"}:
                    values = deltas[model, j, metric]
                    new = observed.get(("candidate", j), {}).get(metric)
                    low, high = ci(values)
                    paired.append({"baseline_or_model": model, "contrast": "candidate_minus_baseline",
                                   "endpoint": endpoint, "metric": metric,
                                   "value": new - point[metric] if new is not None and point[metric] is not None else None,
                                   "ci_low": low, "ci_high": high, "replicates": len(values)})
    aggregates, means = [], {}
    for model in models:
        f1 = [row["f1"] for (key, _), row in observed.items() if key == model]
        means[model] = float(np.mean(f1)) if f1 else None
    for model in models:
        low, high = ci(macro[model])
        dlo, dhi = ci(macro_delta[model])
        delta = means["candidate"] - means[model] if model in {"P6", "P8"} and means[model] is not None else None
        aggregates.append({"model": model, "endpoints": "|".join(e for e, flag in zip(endpoints, supported, strict=True) if flag),
                           "macro_f1": means[model], "ci_low": low, "ci_high": high, "candidate_minus_baseline": delta,
                           "paired_ci_low": dlo, "paired_ci_high": dhi, "paired_replicates": len(macro_delta[model])})
    return rows, paired, aggregates


def write_csv(path, rows):
    with path.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def run(bank, assets, candidate, selection, out):
    cfg = json.loads(PROTOCOL.read_bytes())
    freeze = json.loads(selection.read_bytes())
    checkpoint = candidate / "best.pt"
    if (freeze["selected_checkpoint_sha256"] != digest(checkpoint)
            or freeze["protocol_sha256"] != digest(PROTOCOL)
            or freeze["selected_training_receipt_sha256"] != digest(candidate / "TRAINING_RECEIPT.json")
            or freeze["selection_source"] != "validation_only"):
        raise ValueError("candidate or selection seal mismatch")
    out.mkdir(mode=0o700, exist_ok=False)
    state = torch.load(checkpoint, map_location="cpu", weights_only=True)
    if state["protocol_sha256"] != digest(PROTOCOL):
        raise ValueError("checkpoint protocol mismatch")
    model = TemporalSpecialist(build_titan_v45_backbone())
    model.load_state_dict(state["state_dict"], strict=True)
    model.cuda().eval()
    endpoints = list(cfg["endpoints"])
    size = cfg["training"]["batch_size"]
    calibration = read_bank(bank, "calibration", state["normalizer"])
    scores, _, _, labels = candidate_scores(model, calibration, size)
    threshold, policy = thresholds_on_calibration(labels, scores, endpoints)
    write_json(out / "FROZEN_CANDIDATE_THRESHOLDS.json", {"candidate_sha256": digest(checkpoint),
               "selection_sha256": digest(selection), "source": "calibration_only", "policy": policy})
    del calibration
    test = read_bank(bank, "test", state["normalizer"])
    scores, ids, people, y = candidate_scores(model, test, size)
    original, released_thresholds, hashes = load_released(assets)
    released, y2, ids2, people2, durations = score_released(original, test, size, endpoints)
    if not all(np.array_equal(left, right) for left, right in ((ids, ids2), (people, people2), (y, y2))):
        raise ValueError("paired holdout row membership differs")
    outputs = {**released, "candidate": scores}
    operating = {profile: np.asarray([released_thresholds[profile][name] for name in endpoints]) for profile in released}
    operating["candidate"] = threshold
    np.savez_compressed(out / "private_test_predictions.npz", exams=ids, patients=people, durations=durations, labels=y, **outputs)
    tables = [[], [], []]
    for scope, keep in (("all", np.ones(len(ids), bool)), ("short_7p335", durations == 917), ("long_10", durations == 1250)):
        if not np.any(keep):
            continue
        result = intervals(y[keep], {name: p[keep] for name, p in outputs.items()}, operating,
                           people[keep], endpoints, cfg["calibration"])
        for table, rows in zip(tables, result, strict=True):
            table.extend({"scope": "WITHIN_CODE_NOT_INSTITUTIONAL_CONFIRMATION", "duration": scope,
                          "ecgs": int(keep.sum()), "patients": len(set(people[keep])), **row} for row in rows)
    names = ("EXTERNAL_PER_CLASS_RESULTS.csv", "PATIENT_BOOTSTRAP_CONFIDENCE_INTERVALS.csv",
             "EXTERNAL_MACRO_F1_COMPARISON.csv")
    for name, rows in zip(names, tables, strict=True):
        write_csv(out / name, rows)
    curve_rows = []
    for i, endpoint in enumerate(endpoints):
        keep = y[:, i] >= 0
        for model_name, values in outputs.items():
            for k in range(101):
                truth, score, t = y[keep, i] == 1, values[keep, i], k / 100
                call = score >= t
                tp = int((call & truth).sum())
                curve_rows.append({"model": model_name, "endpoint": endpoint, "threshold": t,
                                   "precision": tp / int(call.sum()) if call.any() else None,
                                   "recall": tp / int(truth.sum()) if truth.any() else None})
    write_csv(out / "PRECISION_RECALL_CURVES.csv", curve_rows)
    report = {"scope": "WITHIN_CODE_NOT_INSTITUTIONAL_CONFIRMATION", "test_ecgs": len(ids), "test_patients": len(set(people)),
              "selection_sha256": digest(selection), "candidate_sha256": digest(checkpoint), "released_assets": hashes,
              "private_prediction_sha256": digest(out / "private_test_predictions.npz"),
              "aggregates": {name: digest(out / name) for name in (*names, "PRECISION_RECALL_CURVES.csv")},
              "independent_generalization": "NOT_EVALUATED"}
    write_json(out / "WITHIN_CODE_EVALUATION_RECEIPT.json", report)
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("bank", "assets", "candidate", "selection", "output"):
        parser.add_argument(key, type=Path)
    args = parser.parse_args()
    run(args.bank, args.assets, args.candidate, args.selection, args.output)
