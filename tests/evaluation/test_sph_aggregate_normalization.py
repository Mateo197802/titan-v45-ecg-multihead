import copy

import pytest

from scripts.external_validation.normalize_sph_aggregate import normalize_metrics, normalize_report


def test_normalizes_from_confusion_counts_without_mutating_input():
    metrics = {"tn": 8, "fp": 2, "fn": 3, "tp": 7, "recall": 0.7, "undefined": {}}
    report = {"schema": "TITAN_V45_SPH_ENDPOINT_RESULTS_V1", "endpoints": {
        "P6:X": {"metrics": metrics, "discordant_exact_duplicate_sensitivity": {"metrics": metrics}}
    }}
    original = copy.deepcopy(report)
    result = normalize_report(report, "a" * 64)
    assert report == original
    assert result["endpoints"]["P6:X"]["metrics"]["sensitivity"] == 0.7
    assert result["endpoints"]["P6:X"]["metrics"]["npv"] == pytest.approx(8 / 11)
    assert result["aggregate_normalization"]["input_sha256"] == "a" * 64


def test_undefined_and_inconsistent_confusion_counts():
    result = normalize_metrics({"tn": 0, "fp": 1, "fn": 0, "tp": 0, "recall": None})
    assert result["sensitivity"] is None and result["npv"] is None
    assert result["undefined"]["npv"] == "zero_denominator"
    with pytest.raises(ValueError, match="recall"):
        normalize_metrics({"tn": 8, "fp": 2, "fn": 3, "tp": 7, "recall": 0.8})
    with pytest.raises(ValueError, match="schema"):
        normalize_report({"schema": "private-ledger"}, "a" * 64)
