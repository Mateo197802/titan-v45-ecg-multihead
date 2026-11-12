from pathlib import Path

import numpy as np


def test_paired_metrics_mask_unknown_and_protect_support(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts/external_validation"))
    from evaluate_code15 import label, paired_metrics

    assert label("False") == 0
    assert label("") == label("unspecified") == -1
    y = np.array([[1, -1], [1, -1], [0, 0], [0, 0], [-1, 0]])
    old = np.array([[.8, .9], [.2, .1], [.2, .2], [.8, .1], [.9, .8]])
    new = np.array([[.8, .9], [.8, .1], [.2, .2], [.2, .1], [.9, .8]])
    config = dict(bootstrap_seed=42, bootstrap_replicates=100,
                  minimum_distinct_positive_and_negative_patients=1,
                  promotion_macro_f1_gain_min=.03, promotion_max_sensitivity_drop=.05,
                  promotion_max_macro_brier_increase=.01, promotion_max_empty_set_rate_increase=.01)
    rows, comparison = paired_metrics(
        y, old, new, np.array(["a", "a", "b", "c", "d"]), np.array([.5, .5]), ["AFIB", "SB"], config,
    )
    assert rows[0]["n_ecg_with_reference"] == 4
    assert rows[0]["n_positive_patients"] == 1
    assert rows[1]["f1"] == 1 and rows[0]["f1"] == .5
    assert rows[2]["estimable"] is False and rows[2]["specificity"] is None
    assert comparison["macro_f1_delta"] == .5 and not comparison["observed_metric_gate_pass"]


def test_bounded_adapter_is_not_unanchored(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts/external_validation"))
    from fit_code_transfer import fit_endpoint, residual_logits

    x = np.array([[-2.], [-1.], [1.], [2.]])
    initial = np.zeros(4)
    theta, iterations = fit_endpoint(x, initial, np.array([0, 0, 1, 1]), np.ones(4),
                                     cap=1.5, l2=.05, maxiter=80)
    adjusted = residual_logits(x, initial, np.zeros(1), np.ones(1), theta, 1.5)
    assert iterations > 0
    assert adjusted[0] < 0 < adjusted[-1]
    assert np.max(np.abs(adjusted)) <= 1.5


def test_independent_verifier_handles_ranking_ties(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts/external_validation"))
    from evaluate_code15 import estimates
    from verify_code15_evaluation import independent_estimates

    y = np.array([1, 0, 1, 0])
    scores = np.array([.8, .8, .7, .1])
    assert independent_estimates(y, scores, .75) == estimates(y, scores >= .75, scores)
