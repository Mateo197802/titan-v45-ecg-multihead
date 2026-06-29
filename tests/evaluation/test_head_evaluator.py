from __future__ import annotations

import numpy as np

from titan_v45.evaluation.heads import evaluate_binary_head, evaluate_binary_heads


def test_binary_head_metrics_include_precision_recall_and_support() -> None:
    report = evaluate_binary_head(
        targets=np.array([1, 1, 0, 0]),
        probabilities=np.array([0.9, 0.4, 0.6, 0.1]),
        threshold=0.5,
    )
    assert report == {
        "tp": 1,
        "tn": 1,
        "fp": 1,
        "fn": 1,
        "support": 4,
        "accuracy": 0.5,
        "precision": 0.5,
        "recall": 0.5,
        "f1": 0.5,
        "threshold": 0.5,
    }


def test_binary_heads_macro_metrics_average_all_declared_classes() -> None:
    targets = np.array([[1, 0], [0, 1], [1, 0], [0, 1]])
    probabilities = np.array([[0.9, 0.1], [0.2, 0.8], [0.8, 0.3], [0.1, 0.9]])
    report = evaluate_binary_heads(
        targets=targets,
        probabilities=probabilities,
        classes=("ASMI", "LVH"),
        thresholds=(0.5, 0.5),
    )
    assert report["macro_f1"] == 1.0
    assert report["mean_accuracy"] == 1.0
    assert tuple(report["classes"]) == ("ASMI", "LVH")
