from __future__ import annotations

import numpy as np

from titan_v45.training.aggregation import aggregate_record_probabilities, clean_top1_predictions


def test_record_aggregation_preserves_first_seen_order() -> None:
    records = ["r2", "r1", "r2"]
    probabilities = np.asarray([[0.2, 0.8], [0.9, 0.1], [0.4, 0.6]])
    aggregated = aggregate_record_probabilities(records, probabilities, reduction="mean")
    assert aggregated.record_ids == ("r2", "r1")
    np.testing.assert_allclose(aggregated.probabilities, [[0.3, 0.7], [0.9, 0.1]])


def test_primary_predictions_are_full_coverage_top1() -> None:
    probabilities = np.asarray([[0.1, 0.7, 0.2], [0.8, 0.1, 0.1]])
    predictions = clean_top1_predictions(probabilities)
    np.testing.assert_array_equal(predictions, [1, 0])
    assert predictions.shape[0] == probabilities.shape[0]
