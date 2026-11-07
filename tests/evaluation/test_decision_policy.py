from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from titan_v45.evaluation.decision_policy import membership_decision

ROOT = Path(__file__).resolve().parents[2]


def test_membership_policy_keeps_all_passing_classes_and_first_class_tie_break() -> None:
    result = membership_decision({"A": 0.8, "B": 0.8}, {"A": 0.7, "B": 0.7})
    assert result == {"top1": "A", "labels": ["A", "B"], "used_fallback": False}


def test_no_pass_falls_back_to_membership_argmax_without_adjusting_thresholds() -> None:
    result = membership_decision({"A": 0.4, "B": 0.6}, {"A": 0.7, "B": 0.9})
    assert result == {"top1": "B", "labels": ["B"], "used_fallback": True}


def test_threshold_equality_is_positive() -> None:
    assert membership_decision({"A": 0.7}, {"A": 0.7})["used_fallback"] is False


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -0.01, 1.01])
def test_invalid_probability_and_threshold_fail_closed(value: float) -> None:
    with pytest.raises(ValueError):
        membership_decision({"A": value}, {"A": 0.7})
    with pytest.raises(ValueError):
        membership_decision({"A": 0.7}, {"A": value})


def test_empty_or_mismatched_class_contract_is_rejected() -> None:
    with pytest.raises(ValueError):
        membership_decision({}, {})
    with pytest.raises(ValueError):
        membership_decision({"A": 0.5}, {"B": 0.5})


def test_fixed_membership_rule_reconstructs_every_archived_p8_decision() -> None:
    metrics = json.loads((ROOT / "outputs/results/external_dev/rhythm_primary8_metrics.json").read_text())
    # Thresholds were already published before this reconstruction audit.
    thresholds = metrics["rhythm"]["thresholds"] if "rhythm" in metrics else metrics["thresholds"]
    with (ROOT / "outputs/results/external_dev/evidence/rhythm_primary8_record_predictions.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    classes = ["AFIB", "SB", "STACH", "NSR", "RBBB", "PAC", "1AVB", "PVC"]
    if isinstance(thresholds, list):
        thresholds = dict(zip(classes, thresholds, strict=True))
    fallback = 0
    for row in rows:
        result = membership_decision({name: float(row["membership_prob_" + name]) for name in classes}, thresholds)
        assert result["top1"] == row["predicted_label"]
        assert set(result["labels"]) == set(row["predicted_labels"].split("|"))
        fallback += result["used_fallback"]
    assert len(rows) == 2193
    assert fallback == 58
