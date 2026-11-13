"""Calibrate a sealed development candidate and compare it once within CODE."""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import torch
from evaluate_released import load_released, score_released
from freeze_candidate import SELECTION
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
    return {**{name: x[name] for name in ("tp", "tn", "fp", "fn", "specificity", "f1", "auroc", "ece")},
            "sensitivity": x["recall"],
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


def within_code_decision(points, aggregates, cfg):
    endpoints = tuple(cfg["endpoints"])
    gate = cfg["promotion"]
    macro = {row["model"]: row for row in aggregates if row["duration"] == "all"}
    scores = {(row["model"], row["endpoint"]): row for row in points if row["duration"] == "all"}
    usable = macro["candidate"]["endpoints"].split("|") == list(endpoints)
    outcome = {"scope": "WITHIN_CODE_NOT_INSTITUTIONAL_CONFIRMATION", "all_five_endpoints_estimable": usable,
               "research_target_met": usable and macro["candidate"]["macro_f1"] >= gate["development_goal_macro_f1"],
               "independent_generalization": "NOT_EVALUATED", "P6_P8_promotion": "NOT_AUTHORIZED_BY_THIS_EVALUATION",
               "P4": "NOT_EVALUABLE", "compared_with": {}}
    for base in ("P6", "P8"):
        if not usable:
            outcome["compared_with"][base] = {"gain_and_safeguards_pass": False, "reason": "unsupported_endpoint"}
            continue
        safeguards = {}
        for endpoint in ("AFIB", "RBBB", "1AVB"):
            for metric, bound in (("sensitivity", "max_sensitivity_drop_afib_rbbb_1avb"),
                                  ("ppv", "max_precision_drop_afib_rbbb_1avb")):
                a, b = (scores[profile, endpoint][metric] for profile in ("candidate", base))
                delta = a - b if a is not None and b is not None else None
                safeguards[f"{endpoint}_{metric}"] = {"delta": delta, "pass": delta is not None and delta >= -gate[bound]}
        brier_delta = float(np.mean([scores["candidate", endpoint]["brier"] - scores[base, endpoint]["brier"]
                                     for endpoint in endpoints]))
        safeguards["macro_brier"] = {"delta": brier_delta, "pass": brier_delta <= gate["max_macro_brier_increase"]}
        delta, low = (macro[base][k] for k in ("candidate_minus_baseline", "paired_ci_low"))
        outcome["compared_with"][base] = {"macro_f1_delta": delta, "paired_ci_low": low, "safeguards": safeguards,
            "gain_and_safeguards_pass": delta >= gate["confirmatory_macro_f1_gain_min"] and low is not None and low > 0
            and all(x["pass"] for x in safeguards.values())}
    outcome["external_adaptation"] = "PASS" if outcome["research_target_met"] and all(
        x["gain_and_safeguards_pass"] for x in outcome["compared_with"].values()) else "FAIL"
    return outcome


def score(bank, assets, candidate, selection, out):
    cfg = json.loads(PROTOCOL.read_bytes())
    freeze = json.loads(selection.read_bytes())
    selection_policy = json.loads(SELECTION.read_bytes())
    checkpoint = candidate / "best.pt"
    if (freeze["selected_checkpoint_sha256"] != digest(checkpoint)
            or freeze["protocol_sha256"] != digest(PROTOCOL)
            or freeze["selection_protocol_sha256"] != digest(SELECTION)
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
    del test
    original, released_thresholds, hashes = load_released(assets)
    baseline = read_bank(bank, "test", selection_policy["released_baseline_normalization"])
    released, y2, ids2, people2, durations = score_released(original, baseline, size, endpoints)
    if not all(np.array_equal(left, right) for left, right in ((ids, ids2), (people, people2), (y, y2))):
        raise ValueError("paired holdout row membership differs")
    outputs = {**released, "candidate": scores}
    operating = {profile: np.asarray([released_thresholds[profile][name] for name in endpoints]) for profile in released}
    operating["candidate"] = threshold
    predictions = out / "private_test_predictions.npz"
    np.savez_compressed(predictions, exams=ids, patients=people, durations=durations, labels=y, **outputs)
    report = {"scope": "WITHIN_CODE_NOT_INSTITUTIONAL_CONFIRMATION", "test_ecgs": len(ids), "test_patients": len(set(people)),
              "selection_sha256": digest(selection), "candidate_sha256": digest(checkpoint), "released_assets": hashes,
              "protocol_sha256": digest(PROTOCOL), "threshold_file_sha256": digest(out / "FROZEN_CANDIDATE_THRESHOLDS.json"),
              "operating_thresholds": {name: values.tolist() for name, values in operating.items()},
              "private_prediction_sha256": digest(predictions), "independent_generalization": "NOT_EVALUATED"}
    write_json(out / "WITHIN_CODE_SCORE_RECEIPT.json", report)
    print(json.dumps(report, sort_keys=True))


def reduce_tables(score_dir, out):
    cfg = json.loads(PROTOCOL.read_bytes())
    endpoints = list(cfg["endpoints"])
    scored = score_dir / "WITHIN_CODE_SCORE_RECEIPT.json"
    receipt = json.loads(scored.read_bytes())
    predictions = score_dir / "private_test_predictions.npz"
    if (digest(predictions) != receipt["private_prediction_sha256"] or digest(PROTOCOL) != receipt["protocol_sha256"]
            or digest(score_dir / "FROZEN_CANDIDATE_THRESHOLDS.json") != receipt["threshold_file_sha256"]):
        raise ValueError("sealed prediction or score protocol mismatch")
    operating = receipt["operating_thresholds"]
    if set(operating) != {"P6", "P8", "candidate"} or any(len(t) != len(endpoints) for t in operating.values()):
        raise ValueError("unregistered model or endpoint threshold roster")
    with np.load(predictions, allow_pickle=False) as archive:
        ids, people, durations, y = (archive[key] for key in ("exams", "patients", "durations", "labels"))
        outputs = {profile: archive[profile] for profile in ("P6", "P8", "candidate")}
    if (not len(ids) == len(people) == len(durations) == len(y) == receipt["test_ecgs"] == len(set(ids))
            or len(set(people)) != receipt["test_patients"] or not np.all(np.isin(durations, [917, 1250]))
            or y.shape != (len(ids), len(endpoints)) or not np.all(np.isin(y, [-1, 0, 1]))
            or any(p.shape != y.shape or not np.isfinite(p).all() or (p < 0).any() or (p > 1).any() for p in outputs.values())):
        raise ValueError("invalid sealed predictions")
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
    decision_file = "WITHIN_CODE_PROMOTION_DECISION.json"
    write_json(out / decision_file, within_code_decision(tables[0], tables[2], cfg))
    curve_rows, calibration_rows = [], []
    for i, endpoint in enumerate(endpoints):
        keep = y[:, i] >= 0
        for model_name, values in outputs.items():
            score = values[keep, i]
            truth = y[keep, i] == 1
            for bin_index in range(10):
                lo, hi = bin_index / 10, (bin_index + 1) / 10
                inside = (score >= lo) & ((score < hi) if bin_index < 9 else (score <= hi))
                count = int(inside.sum())
                calibration_rows.append({"model": model_name, "endpoint": endpoint, "low": lo, "high": hi,
                                         "ecgs": count, "small_bin_suppressed": count < 10,
                                         "mean_score": float(score[inside].mean()) if count >= 10 else None,
                                         "observed_fraction": float(truth[inside].mean()) if count >= 10 else None})
            for k in range(101):
                t = k / 100
                call = score >= t
                tp = int((call & truth).sum())
                curve_rows.append({"model": model_name, "endpoint": endpoint, "threshold": t,
                                   "precision": tp / int(call.sum()) if call.any() else None,
                                   "recall": tp / int(truth.sum()) if truth.any() else None})
    write_csv(out / "PRECISION_RECALL_CURVES.csv", curve_rows)
    write_csv(out / "CALIBRATION_CURVES.csv", calibration_rows)
    report = {**receipt, "score_receipt_sha256": digest(scored),
              "aggregates": {name: digest(out / name) for name in (
                  *names, "PRECISION_RECALL_CURVES.csv", "CALIBRATION_CURVES.csv", decision_file)}}
    write_json(out / "WITHIN_CODE_EVALUATION_RECEIPT.json", report)
    print(json.dumps(report, sort_keys=True))


def reduce(score_dir, output):
    if output.exists():
        raise FileExistsError(output)
    with TemporaryDirectory(prefix="within-code-reduction-", dir=output.parent) as temp:
        staging = Path(temp) / "public"
        staging.mkdir(mode=0o700)
        reduce_tables(score_dir, staging)
        staging.rename(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    inference = sub.add_parser("score")
    for key in ("bank", "assets", "candidate", "selection", "output"):
        inference.add_argument(key, type=Path)
    reduction = sub.add_parser("reduce")
    for key in ("score_dir", "output"):
        reduction.add_argument(key, type=Path)
    args = parser.parse_args()
    if args.command == "score":
        score(args.bank, args.assets, args.candidate, args.selection, args.output)
    else:
        reduce(args.score_dir, args.output)
