from __future__ import annotations

from collections.abc import Sequence

import numpy as np


def apply_binary_thresholds(
    probabilities: np.ndarray, thresholds: Sequence[float]
) -> np.ndarray:
    values = np.asarray(probabilities, dtype=np.float64)
    cuts = np.asarray(tuple(thresholds), dtype=np.float64)
    if values.ndim != 2 or cuts.shape != (values.shape[1],):
        raise ValueError("threshold count must equal the probability width")
    return (values >= cuts[None, :]).astype(np.int64)


def _binary_f1(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    true_positive = int(np.sum((y_true == 1) & (y_pred == 1)))
    false_positive = int(np.sum((y_true == 0) & (y_pred == 1)))
    false_negative = int(np.sum((y_true == 1) & (y_pred == 0)))
    denominator = 2 * true_positive + false_positive + false_negative
    return 0.0 if denominator == 0 else (2.0 * true_positive) / denominator


def tune_binary_thresholds(
    y_true: np.ndarray,
    probabilities: np.ndarray,
    *,
    grid: np.ndarray | None = None,
) -> tuple[float, ...]:
    labels = np.asarray(y_true, dtype=np.int64)
    scores = np.asarray(probabilities, dtype=np.float64)
    if labels.shape != scores.shape or labels.ndim != 2:
        raise ValueError("labels and probabilities must be equally shaped 2D arrays")
    candidates = (
        np.asarray(grid, dtype=np.float64)
        if grid is not None
        else np.linspace(0.05, 0.95, 181, dtype=np.float64)
    )
    if candidates.ndim != 1 or candidates.size == 0:
        raise ValueError("threshold grid must be a non-empty one-dimensional array")
    thresholds: list[float] = []
    for class_index in range(labels.shape[1]):
        best_threshold = float(candidates[0])
        best_f1 = -1.0
        for threshold in candidates:
            f1 = _binary_f1(
                labels[:, class_index],
                (scores[:, class_index] >= float(threshold)).astype(np.int64),
            )
            if f1 > best_f1:
                best_f1 = f1
                best_threshold = float(threshold)
        thresholds.append(best_threshold)
    return tuple(thresholds)
