from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

import numpy as np

from titan_v45.contracts.profiles import CANONICAL_PROFILES
from titan_v45.evaluation.metrics import confusion_matrix_with_labels, metric_gate_status
from titan_v45.evaluation.registry import CANONICAL_RESULTS

GATES = {
    "rhythm_primary8": (0.95, 0.75),
    "rhythm_primary6_diagnostic": (0.95, 0.80),
    "pathology_primary4": (0.90, 0.70),
}


def _macro_f1(true: np.ndarray, pred: np.ndarray, class_count: int) -> float:
    values: list[float] = []
    for index in range(class_count):
        tp = int(np.sum((true == index) & (pred == index)))
        fp = int(np.sum((true != index) & (pred == index)))
        fn = int(np.sum((true == index) & (pred != index)))
        precision = float(tp / (tp + fp)) if tp + fp else 0.0
        recall = float(tp / (tp + fn)) if tp + fn else 0.0
        values.append(
            float(2 * precision * recall / (precision + recall)) if precision + recall else 0.0
        )
    return float(np.mean(values)) if values else 0.0


def evaluate_primary_predictions(
    *, y_true: np.ndarray, y_pred: np.ndarray, classes: Sequence[str], scope: str
) -> dict[str, object]:
    if scope not in {"internal", "external_dev", "source_cv"}:
        raise ValueError("scope must be internal, external_dev, or source_cv")
    true = np.asarray(y_true, dtype=np.int64).reshape(-1)
    pred = np.asarray(y_pred, dtype=np.int64).reshape(-1)
    matrix = confusion_matrix_with_labels(y_true=true, y_pred=pred, labels=classes)
    return {
        "scope": scope,
        "classes": list(classes),
        "records": int(true.size),
        "coverage": 1.0,
        "accuracy": float(np.mean(true == pred)) if true.size else 0.0,
        "macro_f1": _macro_f1(true, pred, len(classes)),
        "decision_rule": "top1",
        "oracle": False,
        "abstention": False,
        "confusion_matrix": matrix.values.tolist(),
    }


def canonical_report(profile_name: str) -> dict[str, object]:
    profile = CANONICAL_PROFILES[profile_name]
    result = CANONICAL_RESULTS[profile_name]
    required_accuracy, required_macro_f1 = GATES[profile_name]
    gate = metric_gate_status(
        accuracy=result.accuracy,
        macro_f1=result.macro_f1,
        required_accuracy=required_accuracy,
        required_macro_f1=required_macro_f1,
    )
    return {
        "profile": profile_name,
        "task": profile.task,
        "classes": list(profile.classes),
        "scope": result.scope,
        "coverage": result.coverage,
        "records": result.records,
        "accuracy": result.accuracy,
        "macro_f1": result.macro_f1,
        "per_class_f1": result.per_class_f1,
        "canonical_status": result.canonical_status,
        "metric_gate": {
            "required_accuracy": required_accuracy,
            "required_macro_f1": required_macro_f1,
            **gate,
        },
        "metric_gate_passed": gate["passed"],
        "decision_rule": "top1" if profile.task == "rhythm" else "classwise_binary",
        "oracle": False,
        "claim_boundary": (
            "external-dev evidence; repeated evaluation prevents an untouched external-final claim"
        ),
    }


def write_canonical_report(profile_name: str, destination: str | Path) -> None:
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(canonical_report(profile_name), indent=2, sort_keys=True) + "\n", encoding="utf-8")
