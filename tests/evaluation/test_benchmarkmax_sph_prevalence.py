from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/benchmarkmax/compare_sph_prevalence_baseline.py"
SPEC = importlib.util.spec_from_file_location("sph_prevalence", SCRIPT)
assert SPEC is not None and SPEC.loader is not None, "prevalence comparison runner is missing"
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_cross_fitted_prevalence_uses_only_calibration_fit_patients():
    patients = np.asarray([f"patient-{index:04d}" for index in range(1000)])
    labels = np.asarray([int(index % 7 == 0) for index in range(1000)])

    scores, folds = MODULE.cross_fitted_prevalence(labels, patients, seed=197802)

    assert np.isfinite(scores).all()
    assert len(folds) == 5
    for fold in folds:
        assert fold["evaluation_support"]["records"] > 0
        assert fold["fit_test_patient_overlap"] == 0
        assert 0.0 < fold["fit_prevalence"] < 1.0
    for fold_index in range(5):
        test_mask = np.asarray(
            [MODULE.calibration.outer_fold(patient, seed=197802) == fold_index for patient in patients]
        )
        fit_mask = np.asarray(
            [
                MODULE.calibration.outer_fold(patient, seed=197802) != fold_index
                and MODULE.calibration.inner_partition(patient, seed=197802) == "calibration_fit"
                for patient in patients
            ]
        )
        assert np.all(scores[test_mask] == labels[fit_mask].mean())


def test_probability_metrics_include_proper_scoring_and_calibration():
    labels = np.asarray([0, 1, 1, 0], dtype=np.int64)
    scores = np.asarray([0.1, 0.8, 0.7, 0.2], dtype=np.float64)

    metrics = MODULE.probability_metrics(labels, scores)

    expected_log_loss = -np.mean(
        labels * np.log(scores) + (1 - labels) * np.log1p(-scores)
    )
    assert metrics["brier"] == pytest.approx(0.045)
    assert metrics["log_loss"] == pytest.approx(expected_log_loss)
    assert metrics["ece"] >= 0.0


def test_constant_prevalence_metrics_are_probability_errors_only():
    labels = np.asarray([1, 0, 0, 0], dtype=np.int64)
    scores = np.full(4, 0.25, dtype=np.float64)

    metrics = MODULE.probability_metrics(labels, scores)

    assert set(metrics) == {"brier", "ece", "log_loss"}
    assert metrics["brier"] == pytest.approx(0.1875)
    assert metrics["ece"] == pytest.approx(0.0)
    assert metrics["log_loss"] > 0.0


def test_cluster_bootstrap_compares_each_model_score_to_prevalence():
    labels = np.asarray([1, 0, 1, 0, 0, 1, 0, 0], dtype=np.int64)
    patients = np.asarray(["p1", "p1", "p2", "p2", "p3", "p4", "p5", "p6"])
    raw = np.asarray([0.8, 0.2, 0.7, 0.3, 0.1, 0.9, 0.2, 0.4])
    prevalence = np.full(labels.size, labels.mean())
    results = MODULE.paired_cluster_bootstrap_deltas(
        labels,
        {
            "raw_v45_oof": raw,
            "platt_oof": raw.copy(),
            "constant_prevalence_oof": prevalence,
        },
        patients,
        replicates=40,
        seed=17,
    )

    assert set(results["comparisons"]) == {"raw_minus_prevalence", "platt_minus_prevalence"}
    assert results["comparisons"]["raw_minus_prevalence"] == results["comparisons"]["platt_minus_prevalence"]


def test_frozen_comparator_rejects_runner_or_verifier_hash_drift():
    config = {"runner_sha256": "0" * 64, "verifier_sha256": "0" * 64}

    with pytest.raises(ValueError, match="runner hash"):
        MODULE.validate_frozen_code(config, SCRIPT, SCRIPT)


def test_frozen_comparator_rejects_verifier_hash_drift():
    verifier = ROOT / "scripts/benchmarkmax/verify_sph_prevalence_comparison.py"
    config = {
        "runner_sha256": MODULE.sha256_file(SCRIPT),
        "verifier_sha256": "0" * 64,
    }

    with pytest.raises(ValueError, match="verifier hash"):
        MODULE.validate_frozen_code(config, SCRIPT, verifier)


def test_frozen_endpoint_order_and_references_match_source_b1_config():
    comparison = json.loads(
        (ROOT / "configs/benchmarkmax/sph_b1_prevalence_comparison.json").read_text()
    )
    source = json.loads((ROOT / "configs/benchmarkmax/sph_b1_calibration.json").read_text())
    actual_targets = [
        {"name": f"{item['profile']}:{item['name']}", "reference": item["reference"]}
        for item in source["endpoints"]
    ]

    assert comparison["endpoints"] == actual_targets
