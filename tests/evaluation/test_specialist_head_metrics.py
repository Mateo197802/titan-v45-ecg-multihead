import pytest

from titan_v45.evaluation.specialist_heads import (
    bootstrap_binary_metrics,
    class_metrics,
    paired_bootstrap_metric_differences,
    select_f1_threshold,
)


def test_threshold_is_selected_on_separable_calibration_scores():
    threshold = select_f1_threshold([0, 0, 1, 1], [0.1, 0.2, 0.8, 0.9])
    assert 0.2 < threshold <= 0.8
    assert class_metrics([0, 0, 1, 1], [0.1, 0.2, 0.8, 0.9], threshold)["f1"] == 1.0


def test_threshold_calibration_requires_both_classes():
    with pytest.raises(ValueError, match="both classes"):
        select_f1_threshold([1, 1], [0.7, 0.8])


def test_class_metrics_include_negative_predictive_value():
    metrics = class_metrics([0, 0, 1, 1], [0.1, 0.8, 0.4, 0.9], 0.5)
    assert metrics["negative_predictive_value"] == 0.5


def test_patient_group_bootstrap_and_paired_difference_are_deterministic():
    truth = [0, 1, 0, 1]
    baseline = [0, 0, 0, 1]
    candidate = [0, 1, 0, 1]
    probabilities = [0.1, 0.4, 0.2, 0.9]
    groups = ["p1", "p1", "p2", "p3"]
    interval = bootstrap_binary_metrics(
        truth, candidate, probabilities, groups, seed=3, n_bootstrap=40
    )
    difference = paired_bootstrap_metric_differences(
        truth, baseline, probabilities, candidate, probabilities, groups,
        seed=3, n_bootstrap=40,
    )
    assert interval["groups"] == 3
    assert interval["intervals"]["f1"]["valid_replicates"] > 0
    assert difference["intervals"]["f1"]["low"] <= difference["intervals"]["f1"]["high"]
