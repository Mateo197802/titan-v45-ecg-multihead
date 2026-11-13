"""Reconcile public PR #10 aggregates without accessing individual predictions."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import subprocess
from itertools import product
from pathlib import Path
from statistics import mean

PRIMARY = "63c74b3fde2c51f7f8cde4ad396d77a1bd16cb29"
SCOPE = "WITHIN_CODE_NOT_INSTITUTIONAL_CONFIRMATION"
MODELS = ("P6", "P8", "candidate")
ENDPOINTS = ("AFIB", "SB", "STACH", "RBBB", "1AVB")
LABELS = {"P6": "Published P6", "P8": "Published P8", "candidate": "Adapted Transformer + ResNet"}
METRICS = ("f1", "auroc", "auprc", "binary_accuracy", "brier", "ece")
BASE = "docs/domain_adaptation"
EVIDENCE = f"{BASE}/evidence"
SOURCE_FILES = {
    name: f"{EVIDENCE}/{name}" for name in (
        "EXTERNAL_PER_CLASS_RESULTS.csv", "PATIENT_BOOTSTRAP_CONFIDENCE_INTERVALS.csv",
        "EXTERNAL_MACRO_F1_COMPARISON.csv", "PRECISION_RECALL_CURVES.csv", "CALIBRATION_CURVES.csv",
        "WITHIN_CODE_EVALUATION_RECEIPT.json", "WITHIN_CODE_INDEPENDENT_READBACK.json",
        "WITHIN_CODE_PROMOTION_DECISION.json", "WITHIN_CODE_SCORE_RECEIPT.json",
        "EXTERNAL_DATA_MANIFESTS_SUMMARY.csv", "PATIENT_AND_SIGNAL_LEAKAGE_AUDIT.json",
        "FROZEN_CANDIDATE_THRESHOLDS.json", "CANDIDATE_SELECTION_RECEIPT.json",
        "PREPROCESSING_REPRODUCIBILITY.json", "SLURM_EXECUTION_LEDGER.csv",
    )
}
SOURCE_FILES.update({name: f"{BASE}/{name}" for name in (
    "FINAL_MODEL_PROMOTION_DECISION.md", "MULTISOURCE_TRAINING_PROTOCOL.json",
)})
NA = "NOT_AVAILABLE"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def csv_rows(data):
    return list(csv.DictReader(io.StringIO(data.decode("utf-8"), newline="")))


def csv_bytes(rows):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def git_blob(repo: Path, commit, path):
    return subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=repo)


def verified_sources(repo):
    if subprocess.check_output(["git", "rev-parse", f"{PRIMARY}^{{commit}}"], cwd=repo).decode().strip() != PRIMARY:
        raise ValueError("primary source commit mismatch")
    return {name: git_blob(repo, PRIMARY, path) for name, path in SOURCE_FILES.items()}


def require(condition, msg):
    if not condition:
        raise ValueError(msg)


def equal(a, b, label):
    require(math.isclose(float(a), float(b), rel_tol=0, abs_tol=1e-12), f"numeric discrepancy: {label}")


def as_keyed(rows, keys):
    lookup = {tuple(row[k] for k in keys): row for row in rows}
    require(len(lookup) == len(rows), "duplicate source metric key")
    return lookup


def matched(row):
    require((row["scope"], row["duration"], row["ecgs"], row["patients"]) == (SCOPE, "all", "4921", "3891"),
            "inconsistent held-out scope or denominator")
    return row


def authenticate(src):
    require(set(src) == set(SOURCE_FILES), "unexpected primary snapshot roster")
    ev, score, readback, qc, frozen, selection, decision = (
        json.loads(src[f"{key}.json"]) for key in (
            "WITHIN_CODE_EVALUATION_RECEIPT", "WITHIN_CODE_SCORE_RECEIPT", "WITHIN_CODE_INDEPENDENT_READBACK",
            "PATIENT_AND_SIGNAL_LEAKAGE_AUDIT", "FROZEN_CANDIDATE_THRESHOLDS", "CANDIDATE_SELECTION_RECEIPT",
            "WITHIN_CODE_PROMOTION_DECISION",
        )
    )
    require(set(ev["aggregates"]) == {
        "EXTERNAL_PER_CLASS_RESULTS.csv", "PATIENT_BOOTSTRAP_CONFIDENCE_INTERVALS.csv",
        "EXTERNAL_MACRO_F1_COMPARISON.csv", "PRECISION_RECALL_CURVES.csv", "CALIBRATION_CURVES.csv",
        "WITHIN_CODE_PROMOTION_DECISION.json",
    }, "evaluation receipt omits primary aggregate evidence")
    for name, digest in ev["aggregates"].items():
        require(sha(src[name]) == digest, f"original aggregate hash mismatch: {name}")
    for name, digest in {
        "WITHIN_CODE_EVALUATION_RECEIPT.json": readback["aggregate_receipt_sha256"],
        "WITHIN_CODE_SCORE_RECEIPT.json": ev["score_receipt_sha256"],
        "EXTERNAL_DATA_MANIFESTS_SUMMARY.csv": qc["public_cohort_counts_sha256"],
        "FROZEN_CANDIDATE_THRESHOLDS.json": ev["threshold_file_sha256"],
        "CANDIDATE_SELECTION_RECEIPT.json": ev["selection_sha256"],
        "MULTISOURCE_TRAINING_PROTOCOL.json": ev["protocol_sha256"],
    }.items():
        require(sha(src[name]) == digest, f"original receipt hash mismatch: {name}")
    require(all(ev[k] == v for k, v in score.items()), "score and aggregation receipts differ")
    require(ev["private_prediction_sha256"] == readback["score_sha256"] and readback["status"] == "PASS"
            and readback["point_comparisons"] == 546 and readback["macro_ci_endpoint_comparisons"] == 30
            and readback["max_abs_point_difference"] <= 1e-12 and readback["max_abs_macro_ci_difference"] == 0,
            "private readback receipt does not authenticate the aggregates")
    require((ev["test_ecgs"], ev["test_patients"], ev["scope"]) == (4921, 3891, SCOPE)
            and (readback["ecgs"], readback["patients"]) == (4921, 3891) and qc["patient_overlap"] == 0
            and qc["protocol_sha256"] == ev["protocol_sha256"] and not qc["independent_institutional_evaluation"]
            and ev["independent_generalization"] == "NOT_EVALUATED",
            "unsupported cohort, overlap or independence claim")
    require(frozen["candidate_sha256"] == ev["candidate_sha256"] == selection["selected_checkpoint_sha256"]
            and frozen["source"] == "calibration_only" and frozen["selection_sha256"] == ev["selection_sha256"],
            "candidate or calibration identity mismatch")
    require(decision["P6_P8_promotion"] == "NOT_AUTHORIZED_BY_THIS_EVALUATION" and decision["P4"] == "NOT_EVALUABLE",
            "source disposition mismatch")
    require(selection["selection_source"] == "validation_only" and decision["external_adaptation"] == "FAIL"
            and not decision["research_target_met"], "source selection or research disposition differs")
    for model in ("P6", "P8"):
        require(not decision["compared_with"][model]["gain_and_safeguards_pass"], "promotion guard unexpectedly passed")
    cohort = as_keyed(csv_rows(src["EXTERNAL_DATA_MANIFESTS_SUMMARY.csv"]), ("split",))
    expected = {"train": (9869, 7808), "validation": (3088, 2426), "calibration": (3080, 2435), "test": (4921, 3891)}
    require(set(cohort) == {(k,) for k in expected}, "invalid split roster")
    for (split,), row in cohort.items():
        ecgs, patients = int(row["ecgs"]), int(row["patients"])
        require((ecgs, patients) == expected[split] and row["source"] == "CODE-15%"
                and int(row["short_7p335_ecgs"]) + int(row["long_10_ecgs"]) == ecgs, "split count mismatch")
    for j, e in enumerate(ENDPOINTS):
        equal(frozen["policy"][e]["threshold"], ev["operating_thresholds"]["candidate"][j], f"{e} threshold")
    return ev


def derive_counts(row):
    tp, tn, fp, fn = (int(row[k]) for k in ("tp", "tn", "fp", "fn"))
    require(min(tp, tn, fp, fn) >= 0 and tp + tn + fp + fn == 4921
            and (tp + fn, tn + fp) == (int(row["positive_ecgs"]), int(row["negative_ecgs"])),
            "confusion matrix denominator mismatch")
    expected = {
        "f1": 2 * tp / (2 * tp + fp + fn), "sensitivity": tp / (tp + fn), "specificity": tn / (tn + fp),
        "ppv": tp / (tp + fp), "npv": tn / (tn + fn), "prevalence": (tp + fn) / 4921,
        "binary_accuracy": (tp + tn) / 4921,
    }
    for k, value in expected.items():
        if k != "binary_accuracy":
            equal(value, row[k], k)
    return expected


def interval(row):
    lo, hi = float(row["ci_low"]), float(row["ci_high"])
    require(-1 <= lo <= hi <= 1 and row["replicates"] == "1000", "invalid patient-bootstrap interval")
    return row["ci_low"], row["ci_high"]


def calculate(src):
    ev = authenticate(src)
    rows = as_keyed([matched(r) for r in csv_rows(src["EXTERNAL_PER_CLASS_RESULTS.csv"]) if r["duration"] == "all"],
                    ("model", "endpoint"))
    require(set(rows) == set(product(MODELS, ENDPOINTS)), "matched table must contain three models and five endpoints")
    boots = as_keyed([matched(r) for r in csv_rows(src["PATIENT_BOOTSTRAP_CONFIDENCE_INTERVALS.csv"])
                     if r["duration"] == "all"], ("baseline_or_model", "contrast", "endpoint", "metric"))
    macro_src = as_keyed([matched(r) for r in csv_rows(src["EXTERNAL_MACRO_F1_COMPARISON.csv"])
                         if r["duration"] == "all"], ("model",))
    point_fields = ("sensitivity", "specificity", "ppv", "npv", *METRICS)
    detailed, macros, comparisons = [], [], []
    for model, endpoint in product(MODELS, ENDPOINTS):
        row = rows[model, endpoint]
        require(row["estimable"] == "True" and all(row[key] == rows["candidate", endpoint][key]
                for key in ("positive_ecgs", "negative_ecgs", "positive_patients", "negative_patients")),
                "not all matched endpoint supports agree")
        equal(row["threshold"], ev["operating_thresholds"][model][ENDPOINTS.index(endpoint)], endpoint)
        counts = derive_counts(row)
        out = {key: row[key] for key in ("model", "endpoint", "ecgs", "patients", "positive_ecgs", "negative_ecgs",
                                         "positive_patients", "negative_patients", "threshold", "tp", "tn", "fp", "fn")}
        for k in point_fields:
            out[k] = counts[k] if k in counts else float(row[k])
            require(0 <= out[k] <= 1, "point metric outside probability range")
            receipt = boots.get((model, "point", endpoint, k))
            if k != "binary_accuracy":
                require(receipt is not None, f"missing original point CI: {model}/{endpoint}/{k}")
            if receipt:
                equal(receipt["value"], out[k], k)
            out[f"{k}_ci_low"], out[f"{k}_ci_high"] = interval(receipt) if receipt else (NA, NA)
        detailed.append(out)
    for model in MODELS:
        row = macro_src[model,]
        require(row["endpoints"] == "|".join(ENDPOINTS), "macro endpoints mismatch")
        per = [r for r in detailed if r["model"] == model]
        global_row = {"model": model, "system": LABELS[model], "ecgs": 4921, "patients": 3891, "endpoints": 5}
        for k in METRICS:
            global_row[f"macro_{k}" if k != "binary_accuracy" else "mean_binary_accuracy"] = mean(r[k] for r in per)
        equal(global_row["macro_f1"], row["macro_f1"], "macro F1")
        require(0 <= float(row["ci_low"]) <= float(row["ci_high"]) <= 1, "invalid macro F1 CI")
        global_row.update(macro_f1_ci_low=row["ci_low"], macro_f1_ci_high=row["ci_high"])
        for k in ("macro_auroc", "macro_auprc", "mean_binary_accuracy", "macro_brier", "macro_ece"):
            global_row[f"{k}_ci_low"] = global_row[f"{k}_ci_high"] = NA
        macros.append(global_row)
    for baseline in MODELS[:2]:
        row = macro_src[baseline,]
        delta = macros[2]["macro_f1"] - macros[MODELS.index(baseline)]["macro_f1"]
        equal(delta, row["candidate_minus_baseline"], "paired macro F1")
        require(-1 <= float(row["paired_ci_low"]) <= float(row["paired_ci_high"]) <= 1
                and row["paired_replicates"] == "1000", "invalid paired macro F1 CI")
        comparisons.append({"baseline": baseline, "comparison": "candidate_minus_baseline", "ecgs": 4921,
                            "patients": 3891, "macro_f1_delta": delta, "paired_ci_low": row["paired_ci_low"],
                            "paired_ci_high": row["paired_ci_high"], "patient_bootstrap_replicates": 1000,
                            **{f"baseline_{key}": macros[MODELS.index(baseline)][key] for key in (
                                "macro_f1", "macro_auroc", "macro_auprc", "mean_binary_accuracy", "macro_brier", "macro_ece")}})
    pr = validate_pr(src, rows)
    return detailed, macros, comparisons, pr


def validate_pr(src, points):
    curves = as_keyed(csv_rows(src["PRECISION_RECALL_CURVES.csv"]), ("model", "endpoint", "threshold"))
    require(len(curves) == 3 * 5 * 101, "unexpected PR grid size")
    for model, endpoint in product(MODELS, ENDPOINTS):
        grid = sorted((r for r in curves.values() if (r["model"], r["endpoint"]) == (model, endpoint)),
                      key=lambda r: float(r["threshold"]))
        require([float(r["threshold"]) for r in grid] == [i / 100 for i in range(101)], "PR threshold grid changed")
        recalls = [float(r["recall"]) for r in grid]
        require(all(0 <= r <= 1 for r in recalls) and all(a >= b for a, b in zip(recalls, recalls[1:], strict=False)),
                "nonmonotone observed PR recall")
        require(all(r["precision"] == "" or 0 <= float(r["precision"]) <= 1 for r in grid),
                "invalid observed PR precision")
        equal(recalls[0], 1, "PR recall at threshold zero")
        equal(grid[0]["precision"], points[model, endpoint]["prevalence"], "PR precision at threshold zero")
        cut = float(points[model, endpoint]["threshold"])
        equivalent = [r for r in grid if float(r["threshold"]) == cut]
        if equivalent:
            equal(equivalent[0]["recall"], points[model, endpoint]["sensitivity"], "PR sensitivity at exact locked cut")
            equal(equivalent[0]["precision"], points[model, endpoint]["ppv"], "PR PPV at exact locked cut")
    return list(curves.values())


def tables(src):
    detailed, macros, comparisons, _ = calculate(src)
    candidate = [row for row in detailed if row["model"] == "candidate"]
    return {
        "PRIMARY_RESULTS_TABLE.csv": csv_bytes(macros),
        "PER_CLASS_RESULTS.csv": csv_bytes(candidate),
        "BASELINE_PER_CLASS_RESULTS.csv": csv_bytes([row for row in detailed if row["model"] != "candidate"]),
        "BASELINE_COMPARISON.csv": csv_bytes(comparisons),
        "SENSITIVITY_PPV.csv": csv_bytes([{k: row[k] for k in (
            "model", "endpoint", "positive_ecgs", "sensitivity", "sensitivity_ci_low", "sensitivity_ci_high",
            "ppv", "ppv_ci_low", "ppv_ci_high")} for row in detailed]),
        "CONFUSION_MATRICES.csv": csv_bytes([{k: row[k] for k in ("endpoint", "tp", "tn", "fp", "fn", "ecgs")}
                                              for row in candidate]),
    }
