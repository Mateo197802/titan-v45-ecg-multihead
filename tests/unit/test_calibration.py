from __future__ import annotations

import numpy as np

from titan_v45.training.calibration import apply_binary_thresholds, tune_binary_thresholds


def test_binary_threshold_tuning_is_deterministic_and_classwise() -> None:
    y_true = np.asarray([[0, 1], [0, 1], [1, 0], [1, 0]], dtype=np.int64)
    y_prob = np.asarray([[0.1, 0.9], [0.2, 0.8], [0.8, 0.2], [0.9, 0.1]])
    first = tune_binary_thresholds(y_true, y_prob, grid=np.asarray([0.25, 0.5, 0.75]))
    second = tune_binary_thresholds(y_true, y_prob, grid=np.asarray([0.25, 0.5, 0.75]))
    assert first == second == (0.25, 0.25)
    np.testing.assert_array_equal(apply_binary_thresholds(y_prob, first), y_true)
