from __future__ import annotations

import copy

import pytest

from titan_v45.benchmarkmax.pac import validate_pac_aggregate


def _report() -> dict:
    supports = {
        "train": {"records": 2, "patients": 2, "positive_records": 1, "positive_patients": 1},
        "development": {"records": 2, "patients": 2, "positive_records": 1, "positive_patients": 1},
        "exploratory_holdout": {
            "records": 2, "patients": 2, "positive_records": 1, "positive_patients": 1,
        },
    }
    metrics = {
        "records": 2,
        "positive_records": 1,
        "negative_records": 1,
        "confusion": {"tp": 1, "fp": 0, "tn": 1, "fn": 0},
        "accuracy": 1.0,
        "sensitivity": 1.0,
        "specificity": 1.0,
        "ppv": 1.0,
        "npv": 1.0,
        "f1": 1.0,
        "auroc": 1.0,
        "average_precision": 1.0,
        "brier": 0.02,
        "ece": 0.1,
        "threshold": 0.5,
    }
    model = {
        "threshold": 0.5,
        "development_average_precision": 0.75,
        "exploratory_holdout_metrics": metrics,
    }
    model_names = {
        "frozen_v45_p8_pac", "logistic_regression",
        *(f"mlp_seed_{seed}" for seed in (197802, 197803, 197804, 197805, 197806)),
    }
    pairs = {
        "logistic_regression_minus_frozen_v45_p8_pac": (
            "frozen_v45_p8_pac", "logistic_regression",
        ),
    }
    for seed in (197802, 197803, 197804, 197805, 197806):
        name = f"mlp_seed_{seed}"
        pairs[f"{name}_minus_frozen_v45_p8_pac"] = ("frozen_v45_p8_pac", name)
        pairs[f"{name}_minus_logistic_regression"] = ("logistic_regression", name)
    metric_names = (
        "accuracy", "sensitivity", "specificity", "ppv", "npv", "f1",
        "auroc", "average_precision", "brier", "ece",
    )
    bootstrap_metrics = {
        name: {
            "point_a": metrics[name],
            "ci95_a": [metrics[name], metrics[name]],
            "point_b": metrics[name],
            "ci95_b": [metrics[name], metrics[name]],
            "delta_b_minus_a": 0.0,
            "delta_ci95": [0.0, 0.0],
            "valid_replicates": 10,
        }
        for name in metric_names
    }
    return {
        "schema": "TITAN_V46_SPH_PAC_HEAD_COMPARISON_V2",
        "scope": "exploratory development only; not independent or confirmatory",
        "inputs": {
            name: "a" * 64
            for name in (
                "metadata", "dictionary", "waveform_archive", "source_inventory",
                "backbone", "p8_specialist", "v45_p8_score_ledger", "v45_p8_scoring_receipt",
            )
        },
        "p8_baseline": {
            "job_id": "32668",
            "ledger_sha256": "a" * 64,
            "receipt_sha256": "a" * 64,
            "checkpoint_sha256": "a" * 64,
            "threshold": 0.45,
        },
        "cohort": {
            "source_records": 6,
            "source_patients": 6,
            "eligible_records": 6,
            "baseline_p8_scores_available_source_records": 6,
            "baseline_p8_common_eligible_records": 6,
            "patient_overlap_across_splits": 0,
            "labels_used_for_split_assignment": False,
            "split_support": supports,
        },
        "models": {
            name: {
                **copy.deepcopy(model),
                "threshold": 0.45 if name == "frozen_v45_p8_pac" else 0.5,
                **({"seed": int(name.removeprefix("mlp_seed_"))} if name.startswith("mlp_seed_") else {}),
                "exploratory_holdout_metrics": {
                    **copy.deepcopy(metrics),
                    "threshold": 0.45 if name == "frozen_v45_p8_pac" else 0.5,
                },
            }
            for name in model_names
        },
        "paired_patient_cluster_bootstrap": {
            "unit": "patient_id cluster; repeated ECGs sampled together",
            "method": "paired unstratified percentile bootstrap",
            "replicates": 10,
            "seed": 197813,
            "comparisons": {
                name: {
                    "reference_model": reference,
                    "candidate_model": candidate,
                    "valid_replicates": 10,
                    "invalid_replicates": 0,
                    "metrics": bootstrap_metrics,
                }
                for name, (reference, candidate) in pairs.items()
            },
        },
        "privacy": {
            "individual_identifiers_exported": False,
            "record_level_scores_exported": False,
            "raw_signals_exported": False,
            "embeddings_exported": False,
        },
    }


def test_public_pac_aggregate_accepts_reconciled_anonymous_report() -> None:
    validate_pac_aggregate(_report())


def test_public_pac_aggregate_rejects_record_level_identifiers() -> None:
    report = _report()
    report["models"]["mlp_seed_197802"]["ecg_ids"] = ["A00001"]

    with pytest.raises(ValueError, match="private|record-level"):
        validate_pac_aggregate(report)


def test_public_pac_aggregate_rejects_inconsistent_holdout_denominator() -> None:
    report = _report()
    report["models"]["mlp_seed_197802"]["exploratory_holdout_metrics"]["records"] = 3

    with pytest.raises(ValueError, match="denominator"):
        validate_pac_aggregate(report)


def test_public_pac_aggregate_requires_every_frozen_mlp_seed() -> None:
    report = _report()
    del report["models"]["mlp_seed_197806"]

    with pytest.raises(ValueError, match="five frozen MLP seeds"):
        validate_pac_aggregate(report)
