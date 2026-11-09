from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import torch

from titan_v45.benchmarkmax.pac import (
    PacMLP,
    assign_patient_split,
    binary_metrics,
    encode_v3f_token_sequences,
    fit_l2_logistic,
    fit_pac_mlp,
    fit_standardizer,
    patient_cluster_bootstrap,
    pool_v3f_meanmax,
    select_f1_threshold,
)
from titan_v45.models.backbone import TitanV4Hybrid

ROOT = Path(__file__).resolve().parents[2]


def _small_backbone() -> TitanV4Hybrid:
    return TitanV4Hybrid(
        morphology_dim=0,
        d_model=16,
        num_transformer_layers=1,
        nhead=4,
        stage_channels=(8, 16, 32, 64),
        dropout=0.0,
    ).eval()


def test_mean_component_matches_existing_single_window_v3f_embedding() -> None:
    torch.manual_seed(197802)
    model = _small_backbone()
    signal = torch.randn(1, 12, 1250)
    mask = torch.ones(1, 12, dtype=torch.bool)

    features = pool_v3f_meanmax(model, signal, mask)
    expected_mean = model.forward_features(signal, lead_mask=mask)

    assert features.shape == (1, 2 * model.d_model)
    torch.testing.assert_close(features[:, : model.d_model], expected_mean, rtol=0, atol=1e-6)
    assert torch.isfinite(features).all()


def test_batched_token_encoder_reconstructs_existing_v3f_embedding() -> None:
    torch.manual_seed(42)
    model = _small_backbone()
    windows = torch.randn(3, 12, 1250)
    masks = torch.ones(3, 12, dtype=torch.bool)

    tokens, mask_context = encode_v3f_token_sequences(model, windows, masks)
    pooled = model.final_norm(tokens.mean(dim=1) + mask_context)
    expected = model.forward_features(windows, lead_mask=masks)

    assert tokens.shape[0] == 3
    assert tokens.shape[2] == model.d_model
    torch.testing.assert_close(pooled, expected, rtol=0, atol=1e-6)


def test_patient_split_matches_existing_frozen_feasibility_assignment() -> None:
    spec = importlib.util.spec_from_file_location(
        "training_feasibility", ROOT / "scripts/benchmarkmax/audit_sph_training_feasibility.py"
    )
    assert spec is not None and spec.loader is not None
    feasibility = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(feasibility)

    for patient_id in ("patient-a", "patient-b", "patient-c"):
        assert assign_patient_split(patient_id) == feasibility.assign_split(patient_id)


def test_f1_threshold_uses_development_scores_and_maximizes_f1() -> None:
    labels = np.asarray([0, 1, 1, 0], dtype=np.int8)
    scores = np.asarray([0.1, 0.8, 0.7, 0.3], dtype=np.float64)

    threshold = select_f1_threshold(labels, scores)

    assert threshold == 0.7


def test_patient_split_rejects_blank_patient_identifier() -> None:
    try:
        assign_patient_split("  ")
    except ValueError as exc:
        assert "patient" in str(exc).lower()
    else:
        raise AssertionError("blank patient identifiers must not be assigned")


def test_binary_metrics_keep_record_counts_and_rank_metrics_distinct() -> None:
    labels = np.asarray([1, 0, 1, 0], dtype=np.int8)
    scores = np.asarray([0.9, 0.1, 0.8, 0.2], dtype=np.float64)

    report = binary_metrics(labels, scores, threshold=0.5)

    assert report["confusion"] == {"tp": 2, "fp": 0, "tn": 2, "fn": 0}
    assert report["f1"] == 1.0
    assert report["auroc"] == 1.0
    assert report["average_precision"] == 1.0


def test_l2_logistic_fits_a_finite_probability_model() -> None:
    features = np.asarray([[-2.0], [-1.0], [1.0], [2.0]], dtype=np.float64)
    labels = np.asarray([0, 0, 1, 1], dtype=np.int8)

    model = fit_l2_logistic(features, labels, c_value=1.0)
    probabilities = model.predict_proba(features)

    assert probabilities.shape == (4,)
    assert np.isfinite(probabilities).all()
    assert probabilities[0] < probabilities[-1]
    assert model.converged


def test_pac_mlp_returns_one_logit_per_record() -> None:
    model = PacMLP(input_dim=1280, hidden_dim=64, dropout=0.2).eval()
    logits = model(torch.zeros(5, 1280))

    assert logits.shape == (5,)
    assert torch.isfinite(logits).all()


def test_feature_standardizer_uses_only_its_fit_input() -> None:
    training = np.asarray([[1.0, 4.0], [3.0, 4.0]])
    scaler = fit_standardizer(training)
    transformed = scaler.transform(training)

    np.testing.assert_allclose(scaler.mean, [2.0, 4.0])
    np.testing.assert_allclose(transformed.mean(axis=0), [0.0, 0.0], atol=1e-12)
    np.testing.assert_allclose(transformed[:, 1], [0.0, 0.0], atol=1e-12)


def test_mlp_fit_is_reproducible_and_uses_dev_only_for_stopping() -> None:
    torch.set_num_threads(1)
    features = np.asarray([[-2.0], [-1.0], [1.0], [2.0], [-1.5], [1.5]])
    labels = np.asarray([0, 0, 1, 1, 0, 1], dtype=np.int8)
    first = fit_pac_mlp(
        features[:4], labels[:4], features[4:], labels[4:],
        seed=197802, max_epochs=4, patience=3, batch_size=2, device="cpu",
    )
    second = fit_pac_mlp(
        features[:4], labels[:4], features[4:], labels[4:],
        seed=197802, max_epochs=4, patience=3, batch_size=2, device="cpu",
    )

    np.testing.assert_array_equal(first.predict_proba(features), second.predict_proba(features))
    assert 1 <= first.epochs_trained <= 4
    assert 0.0 <= first.best_dev_average_precision <= 1.0


def test_patient_bootstrap_is_paired_deterministic_and_reports_invalid_draws() -> None:
    labels = np.asarray([1, 0, 1, 0], dtype=np.int8)
    scores_a = np.asarray([0.9, 0.1, 0.8, 0.2], dtype=np.float64)
    scores_b = np.asarray([0.8, 0.2, 0.7, 0.3], dtype=np.float64)
    patients = np.asarray(["p1", "p2", "p3", "p4"])

    first = patient_cluster_bootstrap(
        labels, scores_a, scores_b, patients, 0.5, 0.5, replicates=40, seed=197813
    )
    second = patient_cluster_bootstrap(
        labels, scores_a, scores_b, patients, 0.5, 0.5, replicates=40, seed=197813
    )

    assert first == second
    assert first["valid_replicates"] + first["invalid_replicates"] == 40
    assert first["metrics"]["auroc"]["delta_b_minus_a"] == 0.0
