import importlib
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts" / "evaluation"


@pytest.fixture
def joint(monkeypatch):
    monkeypatch.syspath_prepend(str(SCRIPTS))
    return importlib.import_module("reviewer_joint_selective")


def test_single_route_has_no_emitted_labels_on_abstention_and_ignores_reference(joint):
    row = {"status": "scored", "profiles": {
        "P6": {"scores": {"c": 0.5}},
        "P8": {"scores": {"a": 0.75}, "labels": ["a"]},
        "P4": {"scores": {"b": 0.6}, "labels": ["b"]},
    }, "reference": {"a": True}}
    thresholds = {"P8": {"a": 0.5}, "P4": {"b": 0.5}}
    cuts = {"P8": 0.25, "P4": 0.125}
    result = joint.classify(row, thresholds, cuts)
    assert result["route"] == "abstained"
    assert result["emitted"] is None
    row["reference"] = {"a": False}
    assert joint.classify(row, thresholds, cuts) == result
    row["profiles"]["P4"]["scores"]["b"] = 0.625
    result = joint.classify(row, thresholds, cuts)
    assert result["signed_margin"] == 0
    assert result["emitted"] == {"P8": ["a"], "P4": ["b"]}
    assert joint.classify({"status": "missing_signal"}, {}, {})["route"] == "not_scored"


def test_positive_accounting_is_not_false_negative_imputation(joint):
    base = {"tn": 1, "fp": 1, "tp": 2, "fn": 2, "n": 6}
    a = {"tn": 1, "fp": 0, "tp": 1, "fn": 1, "n": 3}
    q = {k: base[k]-a[k] for k in base}
    result = joint.positive_accounting({"endpoints": {"X": {
        "held_statement_positive": 5, "routes": {"accepted": a, "abstained": q, "baseline": base},
    }}})
    assert result["X"]["accepted_emitted_missed_positive"] == 1
    assert result["X"]["abstained_reference_positive_no_prediction"] == 2
    assert result["X"]["technically_unscored_reference_positive_no_prediction"] == 1
    assert result["X"]["abstained_baseline_counterfactual_fn"] == 1
    assert result["X"]["fraction_of_held_statement_positives_correctly_emitted"] == 0.2
