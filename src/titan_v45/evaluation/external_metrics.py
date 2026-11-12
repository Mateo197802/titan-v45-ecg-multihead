"""Recompute confusion-derived metrics without imputing unsupported endpoints."""
from __future__ import annotations


def from_confusion(tp: int, fp: int, tn: int, fn: int) -> dict[str, float | None]:
    counts = (tp, fp, tn, fn)
    if any(type(value) is not int or value < 0 for value in counts):
        raise ValueError("confusion counts must be nonnegative integers")

    def ratio(num, denom):
        return num / denom if denom else None

    sensitivity = ratio(tp, tp + fn)
    specificity = ratio(tn, tn + fp)
    supported = sensitivity is not None and specificity is not None
    return {
        "accuracy": ratio(tp + tn, sum(counts)),
        "balanced_accuracy": (sensitivity + specificity) / 2 if supported else None,
        "sensitivity": sensitivity,
        "specificity": specificity,
        "precision": ratio(tp, tp + fp),
        "npv": ratio(tn, tn + fn),
        "f1": ratio(2 * tp, 2 * tp + fp + fn) if supported else None,
    }
