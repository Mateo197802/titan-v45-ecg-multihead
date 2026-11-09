"""Run nested patient-grouped calibration diagnostics on frozen V4.5 SPH scores."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import subprocess
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUTER_FOLDS = 5
MAX_PLATT_SLOPE = 20.0
MIN_PLATT_SLOPE = 0.05
PROBABILITY_EPSILON = 1e-6
ECE_BINS = 10
BOOTSTRAP_METRICS = (
    "accuracy",
    "sensitivity",
    "specificity",
    "ppv",
    "npv",
    "f1",
    "auroc",
    "average_precision",
    "brier",
    "ece",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _bucket(patient_id: str, namespace: str, seed: int, modulus: int) -> int:
    if not patient_id.strip() or modulus < 2:
        raise ValueError("patient ID and valid bucket count are required")
    raw = f"{namespace}{seed}:{patient_id.strip()}".encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big") % modulus


def outer_fold(patient_id: str, *, seed: int = 197802) -> int:
    return _bucket(patient_id, "TITAN-V46-B1-OUTER-V1:", seed, OUTER_FOLDS)


def inner_partition(patient_id: str, *, seed: int = 197802) -> str:
    bucket = _bucket(patient_id, "TITAN-V46-B1-INNER-V1:", seed, 4)
    return "threshold_tune" if bucket == 3 else "calibration_fit"


def _validate_binary_inputs(
    y_true: np.ndarray, probabilities: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    raw_labels = np.asarray(y_true)
    scores = np.asarray(probabilities, dtype=np.float64)
    if raw_labels.ndim != 1 or scores.shape != raw_labels.shape or raw_labels.size == 0:
        raise ValueError("labels and probabilities must be non-empty, equally shaped vectors")
    if not np.isfinite(raw_labels).all() or not np.isin(raw_labels, (0, 1)).all():
        raise ValueError("labels must be binary")
    if not np.isfinite(scores).all() or np.any((scores < 0) | (scores > 1)):
        raise ValueError("probabilities must be finite and in [0, 1]")
    labels = raw_labels.astype(np.int64)
    return labels, scores


def fit_platt(y_true: np.ndarray, probabilities: np.ndarray) -> tuple[float, float]:
    labels, scores = _validate_binary_inputs(y_true, probabilities)
    if np.unique(labels).size != 2:
        raise ValueError("Platt calibration requires both reference classes")

    from scipy.optimize import minimize
    from scipy.special import expit

    clipped = np.clip(scores, PROBABILITY_EPSILON, 1.0 - PROBABILITY_EPSILON)
    logits = np.log(clipped) - np.log1p(-clipped)

    def objective(parameters: np.ndarray) -> tuple[float, np.ndarray]:
        intercept = float(parameters[0])
        slope = float(np.exp(parameters[1]))
        linear = intercept + slope * logits
        fitted = expit(linear)
        loss = float(np.mean(np.logaddexp(0.0, linear) - labels * linear))
        residual = fitted - labels
        gradient = np.array(
            [np.mean(residual), np.mean(residual * slope * logits)], dtype=np.float64
        )
        return loss, gradient

    result = minimize(
        objective,
        np.zeros(2, dtype=np.float64),
        method="L-BFGS-B",
        jac=True,
        bounds=(
            (-20.0, 20.0),
            (math.log(MIN_PLATT_SLOPE), math.log(MAX_PLATT_SLOPE)),
        ),
        options={"maxiter": 1000, "ftol": 1e-12},
    )
    if not result.success or not np.isfinite(result.x).all():
        raise ValueError(f"Platt optimization failed: {result.message}")
    return float(result.x[0]), float(np.exp(result.x[1]))


def apply_platt(
    probabilities: np.ndarray, intercept: float, slope: float
) -> np.ndarray:
    from scipy.special import expit

    scores = np.asarray(probabilities, dtype=np.float64)
    if not np.isfinite(scores).all() or np.any((scores < 0) | (scores > 1)):
        raise ValueError("probabilities must be finite and in [0, 1]")
    if not math.isfinite(intercept) or not MIN_PLATT_SLOPE <= slope <= MAX_PLATT_SLOPE:
        raise ValueError("invalid Platt parameters")
    clipped = np.clip(scores, PROBABILITY_EPSILON, 1.0 - PROBABILITY_EPSILON)
    logits = np.log(clipped) - np.log1p(-clipped)
    return expit(intercept + slope * logits)


def select_f1_threshold(y_true: np.ndarray, probabilities: np.ndarray) -> float:
    labels, scores = _validate_binary_inputs(y_true, probabilities)
    if not np.any(labels == 1):
        raise ValueError("threshold tuning requires positive reference support")
    candidates = np.concatenate(
        (np.unique(scores), [np.nextafter(float(np.max(scores)), math.inf)])
    )
    best_threshold = float(candidates[0])
    best_f1 = -1.0
    for threshold in candidates:
        predicted = scores >= threshold
        tp = int(np.sum((labels == 1) & predicted))
        fp = int(np.sum((labels == 0) & predicted))
        fn = int(np.sum((labels == 1) & ~predicted))
        denominator = 2 * tp + fp + fn
        f1 = 0.0 if denominator == 0 else 2.0 * tp / denominator
        if f1 > best_f1 or (f1 == best_f1 and threshold > best_threshold):
            best_f1 = f1
            best_threshold = float(threshold)
    return best_threshold


def binary_metrics(
    y_true: np.ndarray,
    probabilities: np.ndarray,
    *,
    threshold: float | None = None,
    decisions: np.ndarray | None = None,
    sample_weight: np.ndarray | None = None,
) -> dict:
    labels, scores = _validate_binary_inputs(y_true, probabilities)
    if (threshold is None) == (decisions is None):
        raise ValueError("provide exactly one of threshold or decisions")
    if decisions is None:
        if not math.isfinite(float(threshold)):
            raise ValueError("threshold must be finite")
        predicted = scores >= float(threshold)
    else:
        predicted = np.asarray(decisions, dtype=bool)
        if predicted.shape != labels.shape:
            raise ValueError("decision vector must match labels")
    if sample_weight is None:
        weights = np.ones(labels.size, dtype=np.int64)
    else:
        original_weights = np.asarray(sample_weight)
        if (
            original_weights.shape != labels.shape
            or not np.isfinite(original_weights).all()
            or np.any(original_weights < 0)
            or not np.equal(original_weights, np.floor(original_weights)).all()
        ):
            raise ValueError("sample weights must be non-negative integers matching labels")
        weights = original_weights.astype(np.int64)

    tp = int(np.sum(weights[(labels == 1) & predicted]))
    fp = int(np.sum(weights[(labels == 0) & predicted]))
    tn = int(np.sum(weights[(labels == 0) & ~predicted]))
    fn = int(np.sum(weights[(labels == 1) & ~predicted]))
    total = tp + fp + tn + fn
    positive = tp + fn
    negative = tn + fp
    predicted_positive = tp + fp
    predicted_negative = tn + fn

    def ratio(numerator: float, denominator: float) -> float | None:
        return None if denominator == 0 else float(numerator / denominator)

    unique_scores, inverse = np.unique(scores, return_inverse=True)
    positive_by_score = np.bincount(
        inverse, weights=weights * labels, minlength=unique_scores.size
    )
    negative_by_score = np.bincount(
        inverse, weights=weights * (1 - labels), minlength=unique_scores.size
    )
    if positive and negative:
        lower_negative = np.cumsum(negative_by_score) - negative_by_score
        auroc = float(
            np.sum(positive_by_score * (lower_negative + 0.5 * negative_by_score))
            / (positive * negative)
        )
        descending_positive = positive_by_score[::-1]
        descending_negative = negative_by_score[::-1]
        cumulative_positive = np.cumsum(descending_positive)
        cumulative_total = cumulative_positive + np.cumsum(descending_negative)
        average_precision = float(
            np.sum(
                (descending_positive / positive)
                * (cumulative_positive / np.maximum(cumulative_total, 1))
            )
        )
    else:
        auroc = None
        average_precision = None if not positive else 1.0

    bin_index = np.minimum((scores * ECE_BINS).astype(np.int64), ECE_BINS - 1)
    bin_count = np.bincount(bin_index, weights=weights, minlength=ECE_BINS)
    bin_positive = np.bincount(
        bin_index, weights=weights * labels, minlength=ECE_BINS
    )
    bin_score = np.bincount(
        bin_index, weights=weights * scores, minlength=ECE_BINS
    )
    occupied = bin_count > 0
    ece = (
        float(
            np.sum(
                (bin_count[occupied] / total)
                * np.abs(
                    bin_positive[occupied] / bin_count[occupied]
                    - bin_score[occupied] / bin_count[occupied]
                )
            )
        )
        if total
        else None
    )
    brier = (
        float(np.sum(weights * (scores - labels) ** 2) / total) if total else None
    )
    f1 = ratio(2 * tp, 2 * tp + fp + fn)
    return {
        "records": total,
        "positive_support": positive,
        "negative_support": negative,
        "predicted_positive_support": predicted_positive,
        "confusion": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
        "accuracy": ratio(tp + tn, total),
        "sensitivity": ratio(tp, positive),
        "specificity": ratio(tn, negative),
        "ppv": ratio(tp, predicted_positive),
        "npv": ratio(tn, predicted_negative),
        "f1": f1,
        "auroc": auroc,
        "average_precision": average_precision,
        "brier": brier,
        "ece": ece,
    }


def parse_codes(raw: str) -> set[int]:
    codes = set()
    for token in raw.split(";"):
        token = token.strip()
        if not token:
            continue
        code = token.split("+", maxsplit=1)[0].strip()
        if not code.isdecimal():
            raise ValueError("invalid source code")
        codes.add(int(code))
    return codes


def paired_cluster_bootstrap_delta(
    labels: np.ndarray,
    raw_scores: np.ndarray,
    calibrated_scores: np.ndarray,
    raw_decisions: np.ndarray,
    calibrated_decisions: np.ndarray,
    patient_ids: np.ndarray,
    *,
    replicates: int,
    seed: int,
) -> dict:
    labels, raw_scores = _validate_binary_inputs(labels, raw_scores)
    _, calibrated_scores = _validate_binary_inputs(labels, calibrated_scores)
    raw_pred = np.asarray(raw_decisions, dtype=bool)
    calibrated_pred = np.asarray(calibrated_decisions, dtype=bool)
    patients = np.asarray(patient_ids, dtype=str)
    if any(value.shape != labels.shape for value in (raw_pred, calibrated_pred, patients)):
        raise ValueError("bootstrap arrays must match label rows")
    if np.any(np.char.str_len(np.char.strip(patients)) == 0):
        raise ValueError("bootstrap requires non-empty patient IDs")
    unique_patients, patient_inverse = np.unique(patients, return_inverse=True)
    if unique_patients.size < 2 or replicates < 1:
        raise ValueError("cluster bootstrap requires multiple patients and replicates")

    rng = np.random.Generator(np.random.PCG64(seed))
    deltas = {name: [] for name in BOOTSTRAP_METRICS}
    for _ in range(replicates):
        selected = rng.integers(0, unique_patients.size, size=unique_patients.size)
        patient_weights = np.bincount(selected, minlength=unique_patients.size)
        row_weights = patient_weights[patient_inverse]
        if not np.any(row_weights):
            continue
        raw = binary_metrics(
            labels, raw_scores, decisions=raw_pred, sample_weight=row_weights
        )
        calibrated = binary_metrics(
            labels,
            calibrated_scores,
            decisions=calibrated_pred,
            sample_weight=row_weights,
        )
        for name in BOOTSTRAP_METRICS:
            if raw[name] is not None and calibrated[name] is not None:
                deltas[name].append(float(calibrated[name] - raw[name]))

    intervals = {}
    for name, values in deltas.items():
        intervals[name] = {
            "valid_replicates": len(values),
            "invalid_replicates": replicates - len(values),
            "bootstrap_mean_difference_calibrated_minus_raw": (
                float(np.mean(values)) if values else None
            ),
            "ci95": (
                [float(np.quantile(values, 0.025)), float(np.quantile(values, 0.975))]
                if values
                else None
            ),
        }
    return {
        "unit": "patient_id cluster; repeated ECGs sampled together",
        "method": "paired unstratified percentile bootstrap",
        "replicates": replicates,
        "seed": seed,
        "intervals": intervals,
    }


def _support(labels: np.ndarray, patients: np.ndarray, mask: np.ndarray) -> dict:
    selected_labels = labels[mask]
    selected_patients = patients[mask]
    positive_patients = np.unique(selected_patients[selected_labels == 1]).size
    return {
        "records": int(mask.sum()),
        "patients": int(np.unique(selected_patients).size),
        "positive_records": int(selected_labels.sum()),
        "negative_records": int(mask.sum() - selected_labels.sum()),
        "positive_patients": int(positive_patients),
    }


def nested_patient_calibration(
    labels: np.ndarray,
    probabilities: np.ndarray,
    patient_ids: np.ndarray,
    *,
    seed: int,
) -> dict:
    labels, probabilities = _validate_binary_inputs(labels, probabilities)
    patients = np.asarray(patient_ids, dtype=str)
    if patients.shape != labels.shape or any(not item.strip() for item in patients):
        raise ValueError("each record requires a patient ID")
    folds = np.asarray([outer_fold(item, seed=seed) for item in patients])
    roles = np.asarray([inner_partition(item, seed=seed) for item in patients])
    calibrated = np.full(labels.shape, np.nan, dtype=np.float64)
    raw_decisions = np.zeros(labels.shape, dtype=bool)
    calibrated_decisions = np.zeros(labels.shape, dtype=bool)
    calibrated_at_half = np.zeros(labels.shape, dtype=bool)
    fold_reports = []

    for fold in range(OUTER_FOLDS):
        test_mask = folds == fold
        fit_mask = ~test_mask & (roles == "calibration_fit")
        tune_mask = ~test_mask & (roles == "threshold_tune")
        if np.any((fit_mask & tune_mask) | (fit_mask & test_mask) | (tune_mask & test_mask)):
            raise AssertionError("nested patient partitions overlap")
        for label, mask in (("fit", fit_mask), ("tune", tune_mask), ("test", test_mask)):
            if np.unique(labels[mask]).size != 2:
                raise ValueError(f"endpoint lacks both statement classes in {label} fold")

        intercept, slope = fit_platt(labels[fit_mask], probabilities[fit_mask])
        calibrated_tune = apply_platt(probabilities[tune_mask], intercept, slope)
        calibrated_test = apply_platt(probabilities[test_mask], intercept, slope)
        raw_threshold = select_f1_threshold(labels[tune_mask], probabilities[tune_mask])
        calibrated_threshold = select_f1_threshold(labels[tune_mask], calibrated_tune)
        calibrated[test_mask] = calibrated_test
        raw_decisions[test_mask] = probabilities[test_mask] >= raw_threshold
        calibrated_decisions[test_mask] = calibrated_test >= calibrated_threshold
        calibrated_at_half[test_mask] = calibrated_test >= 0.5
        fold_reports.append(
            {
                "fold": fold,
                "support": {
                    "fit": _support(labels, patients, fit_mask),
                    "threshold_tune": _support(labels, patients, tune_mask),
                    "test": _support(labels, patients, test_mask),
                },
                "selected_thresholds": {
                    "raw_probability_max_f1": raw_threshold,
                    "platt_probability_max_f1": calibrated_threshold,
                },
                "platt_parameters": {"intercept": intercept, "slope": slope},
            }
        )

    if not np.isfinite(calibrated).all():
        raise AssertionError("nested calibration did not produce one prediction per record")
    return {
        "calibrated_probabilities": calibrated,
        "raw_threshold_decisions": raw_decisions,
        "calibrated_threshold_decisions": calibrated_decisions,
        "calibrated_half_decisions": calibrated_at_half,
        "fold_reports": fold_reports,
    }


def _load_metadata(path: Path) -> tuple[dict[str, dict], dict[str, str]]:
    metadata = {}
    patients = {}
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"ECG_ID", "Patient_ID", "AHA_Code"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("SPH metadata is missing required columns")
        for row in reader:
            record_id = row["ECG_ID"].strip()
            patient_id = row["Patient_ID"].strip()
            if not record_id or not patient_id or record_id in metadata:
                raise ValueError("SPH metadata has missing or duplicate identifiers")
            metadata[record_id] = {"codes": parse_codes(row["AHA_Code"])}
            patients[record_id] = patient_id
    return metadata, patients


def _load_ledger(path: Path, targets: list[dict]) -> dict[str, dict]:
    ledger = {}
    for line in path.open(encoding="utf-8"):
        row = json.loads(line)
        record_id = row.get("record_id")
        if not record_id or record_id in ledger or row.get("status") != "scored":
            raise ValueError("SPH ledger has missing, duplicate, or unscored rows")
        profiles = row.get("profiles", {})
        for target in targets:
            profile = profiles.get(target["profile"], {})
            scores = profile.get("scores", {})
            score = scores.get(target["name"])
            if not isinstance(score, (int, float)) or not math.isfinite(score) or not 0 <= score <= 1:
                raise ValueError("SPH ledger has an invalid target probability")
        ledger[record_id] = profiles
    return ledger


def _validate_inputs(
    metadata_path: Path,
    ledger_path: Path,
    v45_config_path: Path,
    receipt_path: Path,
    baseline_path: Path,
    b1_config_path: Path,
) -> tuple[dict, dict, dict, dict, dict]:
    config = json.loads(b1_config_path.read_text(encoding="utf-8"))
    if tuple(config.get("bootstrap", {}).get("delta_metrics", ())) != BOOTSTRAP_METRICS:
        raise ValueError("B1 bootstrap metric list differs from the frozen implementation")
    expected = config["input_sha256"]
    actual = {
        "metadata": sha256_file(metadata_path),
        "ledger": sha256_file(ledger_path),
        "v45_frozen_config": sha256_file(v45_config_path),
        "scoring_receipt": sha256_file(receipt_path),
        "baseline_aggregate": sha256_file(baseline_path),
    }
    if actual != expected:
        raise ValueError("one or more frozen B1 input hashes do not match")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("ledger_sha256") != actual["ledger"]:
        raise ValueError("scoring receipt does not identify the private prediction ledger")
    if receipt.get("source_sha256", {}).get("metadata.csv") != actual["metadata"]:
        raise ValueError("scoring receipt does not identify the SPH metadata")
    v45_config = json.loads(v45_config_path.read_text(encoding="utf-8"))
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    if receipt.get("protocol_commit") != config["source"]["v45_protocol_commit"]:
        raise ValueError("scoring receipt protocol commit differs from the frozen B1 source")
    if receipt.get("protocol_sha256") != config["source"]["v45_protocol_config_sha256"]:
        raise ValueError("scoring receipt protocol hash differs from the frozen B1 source")
    if v45_config.get("expected_source_records") != config["expected_records"]:
        raise ValueError("V4.5 frozen protocol has a different source population")
    if receipt.get("model_sha256") != v45_config.get("model_sha256"):
        raise ValueError("scoring receipt model hashes differ from frozen V4.5 configuration")
    if baseline.get("scoring_ledger_sha256") != actual["ledger"]:
        raise ValueError("baseline aggregate does not identify the private ledger")
    if baseline.get("scoring_receipt_sha256") != actual["scoring_receipt"]:
        raise ValueError("baseline aggregate does not identify the scoring receipt")
    return config, receipt, v45_config, baseline, actual


def build_report(
    metadata_path: Path,
    ledger_path: Path,
    v45_config_path: Path,
    receipt_path: Path,
    baseline_path: Path,
    b1_config_path: Path,
    *,
    script_path: Path,
    slurm_job_id: str,
    commit: str,
) -> dict:
    config, receipt, v45_config, baseline, hashes = _validate_inputs(
        metadata_path,
        ledger_path,
        v45_config_path,
        receipt_path,
        baseline_path,
        b1_config_path,
    )
    metadata, patients_by_record = _load_metadata(metadata_path)
    ledger = _load_ledger(ledger_path, config["endpoints"])
    if metadata.keys() != ledger.keys():
        raise ValueError("metadata and private prediction ledger record sets differ")
    if (
        len(metadata) != config["expected_records"]
        or len(metadata) != config["source"]["records"]
        or len(set(patients_by_record.values())) != config["source"]["patients"]
    ):
        raise ValueError("SPH source population differs from the frozen B1 configuration")

    endpoints = {}
    for index, target in enumerate(config["endpoints"]):
        profile = target["profile"]
        name = target["name"]
        code = int(target["code"])
        key = f"{profile}:{name}"
        frozen_threshold = v45_config["thresholds"][profile][name]
        source_definition = next(
            item
            for item in v45_config["endpoints"]
            if item["profile"] == profile and item["name"] == name
        )
        if source_definition["codes"] != [code] or not math.isclose(
            frozen_threshold, target["v45_frozen_threshold"], rel_tol=0.0, abs_tol=1e-15
        ):
            raise ValueError(f"B1 target {key} differs from the frozen V4.5 contract")

        record_ids = list(metadata)
        y = np.asarray([int(code in metadata[item]["codes"]) for item in record_ids], dtype=np.int64)
        patient_ids = np.asarray([patients_by_record[item] for item in record_ids], dtype=str)
        profile_rows = [ledger[item][profile] for item in record_ids]
        scores = np.asarray(
            [float(row["scores"][name]) for row in profile_rows], dtype=np.float64
        )
        published_decisions = np.asarray(
            [name in row["labels"] for row in profile_rows], dtype=bool
        )
        fallback_target_decisions = int(
            sum(bool(row["used_fallback"]) and name in row["labels"] for row in profile_rows)
        )
        baseline_expected = baseline["endpoints"][key]
        baseline_expected = baseline_expected["metrics"]
        frozen_metrics = binary_metrics(y, scores, decisions=published_decisions)
        for metric in ("tp", "fp", "tn", "fn"):
            if frozen_metrics["confusion"][metric] != baseline_expected[metric]:
                raise ValueError(f"ledger reconciliation failed for {key} {metric}")

        nested = nested_patient_calibration(
            y, scores, patient_ids, seed=int(config["seed"])
        )
        calibrated_scores = nested["calibrated_probabilities"]
        raw_cv_metrics = binary_metrics(
            y,
            scores,
            decisions=nested["raw_threshold_decisions"],
        )
        platt_cv_metrics = binary_metrics(
            y,
            calibrated_scores,
            decisions=nested["calibrated_threshold_decisions"],
        )
        platt_half_metrics = binary_metrics(
            y, calibrated_scores, decisions=nested["calibrated_half_decisions"]
        )
        bootstrap = paired_cluster_bootstrap_delta(
            y,
            scores,
            calibrated_scores,
            nested["raw_threshold_decisions"],
            nested["calibrated_threshold_decisions"],
            patient_ids,
            replicates=int(config["bootstrap"]["replicates"]),
            seed=int(config["bootstrap"]["base_seed"]) + index,
        )
        for metric, interval in bootstrap["intervals"].items():
            raw_value = raw_cv_metrics[metric]
            calibrated_value = platt_cv_metrics[metric]
            interval["point_difference_calibrated_minus_raw"] = (
                None
                if raw_value is None or calibrated_value is None
                else float(calibrated_value - raw_value)
            )
        all_fold_reports = nested["fold_reports"]
        threshold_values_raw = [
            item["selected_thresholds"]["raw_probability_max_f1"]
            for item in all_fold_reports
        ]
        threshold_values_platt = [
            item["selected_thresholds"]["platt_probability_max_f1"]
            for item in all_fold_reports
        ]
        slope_values = [item["platt_parameters"]["slope"] for item in all_fold_reports]
        endpoints[key] = {
            "reference": target["reference"],
            "source_support": {
                "records": int(y.size),
                "patients": int(np.unique(patient_ids).size),
                "positive_records": int(y.sum()),
                "negative_records": int(y.size - y.sum()),
                "patients_with_positive_records": int(np.unique(patient_ids[y == 1]).size),
                "patients_with_negative_records": int(np.unique(patient_ids[y == 0]).size),
            },
            "v45_frozen_baseline": {
                "decision_source": "saved V4.5 labels, including the existing P8 fallback where applicable",
                "frozen_threshold": float(frozen_threshold),
                "fallback_target_decisions": fallback_target_decisions,
                "metrics": frozen_metrics,
            },
            "raw_nested_cv": {
                "metrics": raw_cv_metrics,
                "threshold_selection": "maximum F1 on disjoint threshold-tuning patients in each outer fold",
                "fold_threshold_quantiles": [
                    float(value)
                    for value in np.quantile(threshold_values_raw, [0.0, 0.5, 1.0])
                ],
            },
            "platt_nested_cv": {
                "metrics": platt_cv_metrics,
                "threshold_selection": "maximum F1 on disjoint threshold-tuning patients in each outer fold",
                "fold_threshold_quantiles": [
                    float(value)
                    for value in np.quantile(threshold_values_platt, [0.0, 0.5, 1.0])
                ],
                "slope_quantiles": [
                    float(value) for value in np.quantile(slope_values, [0.0, 0.5, 1.0])
                ],
            },
            "platt_at_0_5_reference_operating_point": {
                "not_a_clinical_threshold": True,
                "metrics": platt_half_metrics,
            },
            "paired_patient_cluster_bootstrap_delta": bootstrap,
            "fold_support": [item["support"] for item in all_fold_reports],
        }

    return {
        "schema": "TITAN_V46_SPH_B1_CALIBRATION_DIAGNOSTIC_V1",
        "scope": (
            "Exploratory V4.6 adaptation diagnostic on previously observed SPH; "
            "not an independent, locked, confirmatory, or clinical validation."
        ),
        "source": {
            "records": len(metadata),
            "patients": len(set(patients_by_record.values())),
            "reference": "presence of the frozen primary code on an ECG; absence is not adjudicated disease absence",
        },
        "design": {
            "frozen_score_source": "V4.5 SPH ledger; weights and raw scores were not changed",
            "method": "positive-slope Platt scaling on score logits",
            "outer_folds": OUTER_FOLDS,
            "patient_assignment_uses_labels": False,
            "fit_tune_test_patient_overlap": 0,
            "approximate_patient_partition": {"fit": 60, "threshold_tune": 20, "outer_evaluation": 20},
            "threshold_objective": "maximum F1 on the separate threshold-tuning partition",
            "calibration_at_0_5": "reported as a descriptive reference point, not clinical decision policy",
            "ece_bins": ECE_BINS,
            "bootstrap": config["bootstrap"],
            "all_spH_already_observed": True,
            "confirmatory_external_test": False,
        },
        "input_sha256": hashes,
        "source_v45_protocol_commit": receipt["protocol_commit"],
        "source_v45_model_sha256": receipt["model_sha256"],
        "individual_identifiers_exported": False,
        "record_level_outputs_exported": False,
        "endpoints": endpoints,
        "execution": {
            "commit": commit,
            "slurm_job_id": slurm_job_id,
            "script_sha256": sha256_file(script_path),
            "b1_config_sha256": sha256_file(b1_config_path),
        },
    }


def _assert_outside(path: Path, roots: list[Path], label: str) -> None:
    resolved = path.resolve()
    for root in roots:
        try:
            resolved.relative_to(root.resolve())
        except ValueError:
            continue
        raise ValueError(f"{label} must remain outside all Git checkouts")


def run(args: argparse.Namespace) -> None:
    output = args.output.resolve()
    roots = [ROOT, *(path.resolve() for path in args.forbidden_root)]
    _assert_outside(output, roots, "private B1 aggregate")
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()
    if status:
        raise ValueError("BenchmarkMax checkout must be clean for frozen B1 execution")
    report = build_report(
        args.metadata,
        args.ledger,
        args.v45_config,
        args.scoring_receipt,
        args.baseline_aggregate,
        args.b1_config,
        script_path=Path(__file__),
        slurm_job_id=os.environ.get("SLURM_JOB_ID", "not_slurm"),
        commit=commit,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    os.chmod(output, 0o600)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--v45-config", type=Path, required=True)
    parser.add_argument("--scoring-receipt", type=Path, required=True)
    parser.add_argument("--baseline-aggregate", type=Path, required=True)
    parser.add_argument("--b1-config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--forbidden-root", type=Path, action="append", default=[])
    run(parser.parse_args())


if __name__ == "__main__":
    main()
