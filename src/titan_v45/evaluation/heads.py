from __future__ import annotations

from collections.abc import Sequence

import numpy as np


def evaluate_binary_head(
    *, targets: np.ndarray, probabilities: np.ndarray, threshold: float
) -> dict[str, float | int]:
    truth = np.asarray(targets, dtype=np.int64).reshape(-1)
    scores = np.asarray(probabilities, dtype=np.float64).reshape(-1)
    if truth.shape != scores.shape or not truth.size:
        raise ValueError("targets and probabilities must have the same non-empty shape")
    if not np.all(np.isin(truth, (0, 1))):
        raise ValueError("binary targets must contain only zero and one")
    predicted = (scores >= float(threshold)).astype(np.int64)
    tp = int(np.sum((truth == 1) & (predicted == 1)))
    tn = int(np.sum((truth == 0) & (predicted == 0)))
    fp = int(np.sum((truth == 0) & (predicted == 1)))
    fn = int(np.sum((truth == 1) & (predicted == 0)))
    precision = float(tp / (tp + fp)) if tp + fp else 0.0
    recall = float(tp / (tp + fn)) if tp + fn else 0.0
    f1 = float(2 * precision * recall / (precision + recall)) if precision + recall else 0.0
    return {
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "support": int(truth.size),
        "accuracy": float((tp + tn) / truth.size),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "threshold": float(threshold),
    }


def evaluate_binary_heads(
    *,
    targets: np.ndarray,
    probabilities: np.ndarray,
    classes: Sequence[str],
    thresholds: Sequence[float],
) -> dict[str, object]:
    truth = np.asarray(targets)
    scores = np.asarray(probabilities)
    if truth.shape != scores.shape or truth.ndim != 2:
        raise ValueError("targets and probabilities must be matching two-dimensional arrays")
    if truth.shape[1] != len(classes) or len(classes) != len(thresholds):
        raise ValueError("class and threshold counts must match the prediction width")
    panels = {
        name: evaluate_binary_head(
            targets=truth[:, index], probabilities=scores[:, index], threshold=thresholds[index]
        )
        for index, name in enumerate(classes)
    }
    return {
        "classes": list(classes),
        "panels": panels,
        "macro_f1": float(np.mean([panel["f1"] for panel in panels.values()])),
        "mean_accuracy": float(np.mean([panel["accuracy"] for panel in panels.values()])),
    }
