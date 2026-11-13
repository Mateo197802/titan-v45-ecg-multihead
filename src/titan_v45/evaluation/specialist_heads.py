"""Metrics and calibration helpers for the new specialist-head pilot."""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np

from titan_v45.evaluation.revision_report import binary_metrics


def select_f1_threshold(truth: Sequence[int], probabilities: Sequence[float]) -> float:
    y = np.asarray(truth, dtype=np.int64)
    scores = np.asarray(probabilities, dtype=np.float64)
    if y.ndim != 1 or scores.shape != y.shape or not len(y):
        raise ValueError("truth and scores must be nonempty aligned vectors")
    if not np.isin(y, (0, 1)).all() or not np.isfinite(scores).all():
        raise ValueError("truth must be binary and scores finite")
    if np.any((scores < 0) | (scores > 1)) or len(np.unique(y)) != 2:
        raise ValueError("threshold calibration requires scores in [0, 1] and both classes")
    candidates = np.unique(np.r_[0.0, scores, 1.0])
    best_threshold, best_f1 = 0.0, -1.0
    for threshold in candidates:
        metrics = binary_metrics(y, scores >= threshold, scores)
        current_f1 = float(metrics["f1"])
        if current_f1 > best_f1 or (current_f1 == best_f1 and threshold > best_threshold):
            best_threshold, best_f1 = float(threshold), current_f1
    return best_threshold


def class_metrics(
    truth: Sequence[int], probabilities: Sequence[float], threshold: float
) -> dict[str, Any]:
    y = np.asarray(truth, dtype=np.int64)
    scores = np.asarray(probabilities, dtype=np.float64)
    if not np.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError("threshold must lie in [0, 1]")
    return _with_negative_predictive_value(binary_metrics(y, scores >= threshold, scores))


def _with_negative_predictive_value(metrics: dict[str, Any]) -> dict[str, Any]:
    denominator = int(metrics["tn"]) + int(metrics["fn"])
    metrics["negative_predictive_value"] = (
        int(metrics["tn"]) / denominator if denominator else None
    )
    return metrics


def _metric_interval(values: dict[str, list[float]], confidence: float, replicates: int) -> dict[str, Any]:
    tail = (1 - confidence) / 2
    result = {}
    for name, samples in values.items():
        low, high = np.quantile(samples, [tail, 1 - tail], method="linear") if samples else (None, None)
        result[name] = {
            "low": None if low is None else float(low),
            "high": None if high is None else float(high),
            "valid_replicates": len(samples),
            "invalid_replicates": replicates - len(samples),
        }
    return result


def bootstrap_binary_metrics(
    truth: Sequence[int],
    predicted: Sequence[int],
    probabilities: Sequence[float],
    group_ids: Sequence[str],
    *,
    seed: int,
    n_bootstrap: int = 2000,
    confidence: float = 0.95,
) -> dict[str, Any]:
    """Percentile intervals from resampling whole patient/record groups."""
    y = np.asarray(truth, dtype=np.int64)
    pred = np.asarray(predicted, dtype=np.int64)
    scores = np.asarray(probabilities, dtype=np.float64)
    groups = np.asarray(group_ids, dtype=str)
    if y.ndim != 1 or pred.shape != y.shape or scores.shape != y.shape or groups.shape != y.shape:
        raise ValueError("bootstrap values and group IDs must be aligned vectors")
    if not len(y) or not np.isin(y, (0, 1)).all() or not np.isin(pred, (0, 1)).all():
        raise ValueError("bootstrap targets and calls must be nonempty and binary")
    if not np.isfinite(scores).all() or np.any((scores < 0) | (scores > 1)):
        raise ValueError("bootstrap probabilities must be finite and in [0, 1]")
    if not np.all(groups) or seed < 0 or n_bootstrap < 1 or not 0 < confidence < 1:
        raise ValueError("invalid bootstrap groups or settings")
    unique = np.unique(groups)
    row_indices = [np.flatnonzero(groups == group) for group in unique]
    names = ("accuracy", "precision", "recall", "specificity", "negative_predictive_value",
             "f1", "auroc", "average_precision", "brier_score", "ece")
    values = {name: [] for name in names}
    rng = np.random.Generator(np.random.PCG64(seed))
    for _ in range(n_bootstrap):
        sampled = rng.integers(0, len(unique), size=len(unique))
        indices = np.concatenate([row_indices[index] for index in sampled])
        metrics = _with_negative_predictive_value(binary_metrics(y[indices], pred[indices], scores[indices]))
        for name in names:
            value = metrics[name]
            if value is not None and np.isfinite(value):
                values[name].append(float(value))
    return {
        "unit": "patient_or_record_group",
        "groups": len(unique),
        "seed": seed,
        "n_bootstrap": n_bootstrap,
        "confidence": confidence,
        "intervals": _metric_interval(values, confidence, n_bootstrap),
    }


def paired_bootstrap_metric_differences(
    truth: Sequence[int],
    baseline_calls: Sequence[int],
    baseline_probabilities: Sequence[float],
    candidate_calls: Sequence[int],
    candidate_probabilities: Sequence[float],
    group_ids: Sequence[str],
    *,
    seed: int,
    n_bootstrap: int = 2000,
    confidence: float = 0.95,
) -> dict[str, Any]:
    y = np.asarray(truth, dtype=np.int64)
    base = np.asarray(baseline_calls, dtype=np.int64)
    base_scores = np.asarray(baseline_probabilities, dtype=np.float64)
    candidate = np.asarray(candidate_calls, dtype=np.int64)
    candidate_scores = np.asarray(candidate_probabilities, dtype=np.float64)
    groups = np.asarray(group_ids, dtype=str)
    if any(values.shape != y.shape for values in (base, base_scores, candidate, candidate_scores, groups)):
        raise ValueError("paired bootstrap inputs and group IDs must be aligned vectors")
    if not len(y) or not np.all(groups) or seed < 0 or n_bootstrap < 1:
        raise ValueError("paired bootstrap requires rows, groups, and valid settings")
    unique = np.unique(groups)
    row_indices = [np.flatnonzero(groups == group) for group in unique]
    names = ("accuracy", "precision", "recall", "specificity", "negative_predictive_value",
             "f1", "auroc", "average_precision", "brier_score", "ece")
    differences = {name: [] for name in names}
    rng = np.random.Generator(np.random.PCG64(seed))
    for _ in range(n_bootstrap):
        sampled = rng.integers(0, len(unique), size=len(unique))
        indices = np.concatenate([row_indices[index] for index in sampled])
        old = _with_negative_predictive_value(
            binary_metrics(y[indices], base[indices], base_scores[indices])
        )
        new = _with_negative_predictive_value(
            binary_metrics(y[indices], candidate[indices], candidate_scores[indices])
        )
        for name in names:
            if old[name] is not None and new[name] is not None:
                delta = float(new[name]) - float(old[name])
                if np.isfinite(delta):
                    differences[name].append(delta)
    return {
        "unit": "paired_patient_or_record_group",
        "groups": len(unique),
        "seed": seed,
        "n_bootstrap": n_bootstrap,
        "confidence": confidence,
        "intervals": _metric_interval(differences, confidence, n_bootstrap),
    }
