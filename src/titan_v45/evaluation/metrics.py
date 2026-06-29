from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class LabeledConfusionMatrix:
    labels: tuple[str, ...]
    values: np.ndarray


def metric_gate_status(
    *, accuracy: float, macro_f1: float, required_accuracy: float, required_macro_f1: float
) -> dict[str, bool]:
    accuracy_pass = float(accuracy) >= float(required_accuracy)
    macro_f1_pass = float(macro_f1) >= float(required_macro_f1)
    return {
        "accuracy_pass": accuracy_pass,
        "macro_f1_pass": macro_f1_pass,
        "passed": accuracy_pass and macro_f1_pass,
    }


def confusion_matrix_with_labels(
    *, y_true: np.ndarray, y_pred: np.ndarray, labels: Sequence[str]
) -> LabeledConfusionMatrix:
    true = np.asarray(y_true, dtype=np.int64)
    pred = np.asarray(y_pred, dtype=np.int64)
    if true.shape != pred.shape:
        raise ValueError("y_true and y_pred must have the same shape")
    matrix = np.zeros((len(labels), len(labels)), dtype=np.int64)
    for expected, observed in zip(true.flat, pred.flat, strict=True):
        if expected < 0 or observed < 0 or expected >= len(labels) or observed >= len(labels):
            raise ValueError("class index is outside the declared label order")
        matrix[int(expected), int(observed)] += 1
    return LabeledConfusionMatrix(labels=tuple(labels), values=matrix)
