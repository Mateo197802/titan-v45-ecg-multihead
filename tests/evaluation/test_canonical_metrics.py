from __future__ import annotations

import numpy as np

from titan_v45.evaluation.metrics import confusion_matrix_with_labels, metric_gate_status
from titan_v45.evaluation.registry import CANONICAL_RESULTS


def test_canonical_results_preserve_observed_values_and_boundaries() -> None:
    assert CANONICAL_RESULTS["rhythm_primary8"].accuracy == 0.9060647514819882
    assert CANONICAL_RESULTS["rhythm_primary8"].macro_f1 == 0.7614253535094375
    assert CANONICAL_RESULTS["rhythm_primary8"].canonical_status == "NO_PASA"

    assert CANONICAL_RESULTS["rhythm_primary6_diagnostic"].accuracy == 0.9519172245891662
    assert CANONICAL_RESULTS["rhythm_primary6_diagnostic"].macro_f1 == 0.8009383239876123

    p4 = CANONICAL_RESULTS["pathology_primary4"]
    assert p4.accuracy == 0.8022904853689048
    assert p4.macro_f1 == 0.793456370406346
    assert p4.coverage == 1.0
    assert p4.canonical_status == "ACEPTADO_POR_DECISION_DEL_PROYECTO"


def test_metric_gate_does_not_promote_project_acceptance_to_metric_pass() -> None:
    decision = metric_gate_status(
        accuracy=0.8022904853689048,
        macro_f1=0.793456370406346,
        required_accuracy=0.90,
        required_macro_f1=0.70,
    )
    assert decision == {"accuracy_pass": False, "macro_f1_pass": True, "passed": False}


def test_confusion_matrix_keeps_declared_class_order() -> None:
    labels = ("SB", "AFIB", "PVC")
    matrix = confusion_matrix_with_labels(
        y_true=np.array([1, 0, 2, 1]),
        y_pred=np.array([1, 2, 2, 0]),
        labels=labels,
    )
    assert matrix.labels == labels
    assert matrix.values.tolist() == [[0, 0, 1], [1, 1, 0], [0, 0, 1]]
