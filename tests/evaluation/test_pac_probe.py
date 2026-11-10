import numpy as np
import pytest

import titan_v45.evaluation.pac_probe as pac_probe
from titan_v45.evaluation.pac_probe import (
    binary_metrics,
    duplicate_balanced_sample_weights,
    fit_logistic_probe,
    fit_mlp_probe,
    patient_cluster_bootstrap,
    patient_group_split,
    pool_record_windows,
    pool_v3f_tokens,
    predict_logistic_probe,
    predict_mlp_probe,
)


def test_v3f_token_pooling_is_mean_plus_max_and_record_windows_are_mean_pooled():
    tokens = np.arange(2 * 3 * 4, dtype=np.float32).reshape(2, 3, 4)
    per_window = pool_v3f_tokens(tokens)
    expected = np.concatenate([tokens.mean(axis=1), tokens.max(axis=1)], axis=1)
    np.testing.assert_array_equal(per_window, expected)

    record = pool_record_windows(per_window)
    np.testing.assert_array_equal(record, expected.mean(axis=0))


def test_patient_split_is_reproducible_and_keeps_patient_and_duplicate_links_together():
    patients = np.array([f"p{i}" for i in range(12)])
    labels = np.array([i % 2 for i in range(12)], dtype=bool)
    hashes = np.array([f"h{i}" for i in range(12)])
    hashes[0], hashes[1] = "same", "same"

    train, holdout = patient_group_split(
        patients, labels, signal_hashes=hashes, train_fraction=0.75, seed=41
    )
    train2, holdout2 = patient_group_split(
        patients, labels, signal_hashes=hashes, train_fraction=0.75, seed=41
    )
    np.testing.assert_array_equal(train, train2)
    np.testing.assert_array_equal(holdout, holdout2)
    assert not set(patients[train]) & set(patients[holdout])
    assert not (0 in train and 1 in holdout or 1 in train and 0 in holdout)
    assert set(train) | set(holdout) == set(range(len(patients)))


def test_patient_split_rejects_missing_labels_and_unsplittable_strata():
    with pytest.raises(ValueError, match="same length"):
        patient_group_split(["p1"], [True, False])
    with pytest.raises(ValueError, match="at least two patient components"):
        patient_group_split(["p1", "p2", "p3"], [True, False, False])


def test_binary_metrics_keep_denominators_and_do_not_invent_auc_for_one_class():
    report = binary_metrics([1, 0, 1, 0], [0.8, 0.2, 0.4, 0.6])
    assert report["support"] == {"positive": 2, "negative": 2}
    assert report["confusion"] == {"tp": 1, "fp": 1, "tn": 1, "fn": 1}
    assert report["accuracy"] == 0.5
    assert report["auroc"] == 0.75
    assert report["average_precision"] == pytest.approx(5 / 6)

    single_class = binary_metrics([1, 1], [0.7, 0.4])
    assert single_class["auroc"] is None
    assert single_class["specificity"] is None


def test_duplicate_weights_balance_training_without_using_other_partitions():
    weights = duplicate_balanced_sample_weights(
        [1, 1, 0, 0], ["repeat", "repeat", "negative-a", "negative-b"]
    )
    assert weights[0] == pytest.approx(weights[1])
    assert weights.sum() == pytest.approx(len(weights))
    assert weights[:2].sum() == pytest.approx(weights[2:].sum())


def test_fixed_probe_trainers_return_finite_probabilities():
    features = np.asarray([[-2, 0], [-1, 1], [1, 0], [2, 1]], dtype=np.float32)
    labels = np.asarray([0, 0, 1, 1], dtype=np.int64)
    weights = np.ones(4, dtype=np.float32)
    logistic = fit_logistic_probe(features, labels, weights)
    logistic_probabilities = predict_logistic_probe(features, logistic)
    assert np.isfinite(logistic_probabilities).all()
    assert logistic_probabilities[0] < logistic_probabilities[-1]

    mlp = fit_mlp_probe(features, labels, weights, epochs=3, batch_size=2, seed=19)
    mlp_probabilities = predict_mlp_probe(features, mlp)
    assert mlp_probabilities.shape == (4,)
    assert np.isfinite(mlp_probabilities).all()


def test_patient_cluster_bootstrap_reports_requested_and_valid_draws():
    report = patient_cluster_bootstrap(
        [0, 1, 0, 1], [0.1, 0.9, 0.2, 0.8], ["p1", "p1", "p2", "p2"],
        replicates=20, seed=4,
    )
    assert report["replicates_requested"] == 20
    interval = report["intervals"]["accuracy"]
    assert interval["valid_replicates"] == 20
    assert interval["invalid_replicates"] == 0


def test_patient_cluster_bootstrap_indexes_groups_without_scanning_all_rows_per_patient(
    monkeypatch,
):
    original = np.flatnonzero
    calls = 0

    def counted_flatnonzero(values):
        nonlocal calls
        calls += 1
        return original(values)

    monkeypatch.setattr(pac_probe.np, "flatnonzero", counted_flatnonzero)
    labels = np.tile([0, 1], 100)
    scores = np.where(labels == 1, 0.8, 0.2)
    patients = np.asarray([f"patient-{index}" for index in range(len(labels))])

    report = patient_cluster_bootstrap(labels, scores, patients, replicates=2, seed=1)

    assert report["replicates_requested"] == 2
    assert calls <= 1
