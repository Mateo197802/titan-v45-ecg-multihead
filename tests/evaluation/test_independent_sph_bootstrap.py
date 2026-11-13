import pytest

from scripts.external_validation.independent_sph_bootstrap import _compare, binary_intervals
from titan_v45.evaluation.sph_report import _cluster_bootstrap


def test_independent_intervals_reproduce_frozen_cluster_draws():
    truth = [1, 0, 1, 0, 1]
    predicted = [1, 1, 0, 0, 1]
    clusters = ["p2", "p2", "p1", "p3", "p4"]
    expected = _cluster_bootstrap(truth, predicted, [0.9, 0.7, 0.2, 0.1, 0.8], clusters,
                                  seed=197813, replicates=75, ece_bins=10)
    independent = binary_intervals(truth, predicted, clusters, 197813, 75)
    _compare(independent, expected)
    expected["f1"]["low"] += 0.1
    with pytest.raises(ValueError, match="bootstrap mismatch"):
        _compare(independent, expected)


def test_independent_intervals_handle_undefined_metrics():
    result = binary_intervals([0, 0], [1, 1], ["a", "b"], 7, 10)
    assert result["sensitivity"]["valid_replicates"] == 0
    assert result["npv"]["valid_replicates"] == 0
    assert result["f1"]["valid_replicates"] == 10
