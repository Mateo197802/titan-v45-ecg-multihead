import numpy as np
import pytest

from scripts.external_validation.evaluate_sph_ece_corrected import corrected_metric_values
from titan_v45.evaluation.revision_report import binary_metrics
from titan_v45.evaluation.sph_report import _metric_values


@pytest.mark.parametrize("weights", [[1, 1, 1, 1, 1, 1], [2, 0, 3, 1, 0, 2]])
def test_weighted_bootstrap_metrics_match_explicit_record_replication(weights):
    truth = np.array([0, 1, 0, 1, 1, 0])
    predicted = np.array([0, 1, 1, 0, 1, 0])
    scores = np.array([0.1, 0.8, 0.8, 0.3, 0.7, 0.2])
    weighted = corrected_metric_values(_metric_values, truth, predicted, scores, weights, 10)
    indices = np.repeat(np.arange(len(truth)), weights)
    expanded = binary_metrics(truth[indices], predicted[indices], scores[indices], ece_bins=10)
    for metric in ("accuracy", "specificity", "precision", "f1", "brier_score", "ece",
                   "auroc", "average_precision"):
        assert weighted[metric] == pytest.approx(expanded[metric])
    assert weighted["sensitivity"] == pytest.approx(expanded["recall"])
    assert weighted["npv"] == pytest.approx(expanded["tn"] / (expanded["tn"] + expanded["fn"]))


def test_original_ece_bin_edge_difference_is_reproducible():
    truth = [0, 1, 0, 1, 1, 0]
    predicted = [0, 1, 1, 0, 1, 0]
    scores = [0.1, 0.8, 0.8, 0.3, 0.7, 0.2]
    original = _metric_values(truth, predicted, scores, [1] * 6, 10)
    point = binary_metrics(truth, predicted, scores, ece_bins=10)
    assert original["ece"] != pytest.approx(point["ece"])


def test_weighted_metrics_explicitly_handle_absent_classes_and_no_predictions():
    values = _metric_values([0, 0], [1, 1], [0.4, 0.6], [1, 1], 10)
    assert values["sensitivity"] is None
    assert values["npv"] is None
    assert values["auroc"] is None
    assert values["average_precision"] is None
