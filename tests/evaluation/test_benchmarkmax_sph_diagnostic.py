import pytest

from scripts.benchmarkmax.audit_sph_baseline import summarize


def test_binned_diagnostic_reconciles_frozen_decisions_and_prevalence():
    rows = [(1, 1, 0.8), (1, 0, 0.4), (0, 1, 0.7), (0, 0, 0.1)]
    expected = {"tp": 1, "tn": 1, "fp": 1, "fn": 1, "rows": 4,
                "auroc": 0.75, "average_precision": 0.8, "brier_score": 0.2, "ece": 0.1}
    result = summarize(rows, expected)
    assert result["statement_prevalence"] == 0.5
    assert result["average_precision_no_skill_baseline"] == 0.5
    assert sum(item["positive"] + item["negative"] for item in result["score_bins_uniform_20"]) == 4
    assert result["exploratory_binned_threshold_curve"][-1]["sensitivity"] == 1.0
    with pytest.raises(ValueError, match="confusion"):
        summarize(rows, {**expected, "fp": 2})
