from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from titan_v45.evaluation.primary import evaluate_primary_predictions, write_canonical_report


def test_primary_evaluator_reports_top1_without_oracle_or_abstention() -> None:
    report = evaluate_primary_predictions(
        y_true=np.array([0, 1, 2, 2]),
        y_pred=np.array([0, 1, 1, 2]),
        classes=("AFIB", "SB", "PVC"),
        scope="internal",
    )
    assert report["accuracy"] == 0.75
    assert report["macro_f1"] == 0.7777777777777777
    assert report["coverage"] == 1.0
    assert report["decision_rule"] == "top1"
    assert report["oracle"] is False
    assert report["abstention"] is False
    assert report["confusion_matrix"] == [[1, 0, 0], [0, 1, 0], [0, 1, 1]]


def test_write_canonical_report_preserves_project_decision(tmp_path: Path) -> None:
    destination = tmp_path / "p4.json"
    write_canonical_report("pathology_primary4", destination)
    payload = json.loads(destination.read_text(encoding="utf-8"))
    assert payload["canonical_status"] == "ACEPTADO_POR_DECISION_DEL_PROYECTO"
    assert payload["metric_gate_passed"] is False
    assert payload["accuracy"] == 0.8022904853689048
