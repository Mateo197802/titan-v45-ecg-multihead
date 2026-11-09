from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/benchmarkmax/verify_sph_prevalence_comparison.py"
SPEC = importlib.util.spec_from_file_location("verify_sph_prevalence", SCRIPT)
assert SPEC is not None and SPEC.loader is not None, "prevalence comparison verifier is missing"
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _valid_fixture():
    config = json.loads(
        (ROOT / "configs/benchmarkmax/sph_b1_prevalence_comparison.json").read_text()
    )
    config["source"].update({"records": 10, "patients": 8})
    config["bootstrap"].update({"replicates": 10, "base_seed": 197823})
    config_sha = "a" * 64
    script_sha = "b" * 64
    metrics = {
        "raw_v45_oof": {
            "brier": 0.2,
            "ece": 0.1,
            "log_loss": 0.6,
        },
        "platt_oof": {
            "brier": 0.18,
            "ece": 0.08,
            "log_loss": 0.55,
        },
        "constant_prevalence_oof": {
            "brier": 0.16,
            "ece": 0.0,
            "log_loss": 0.5,
        },
    }
    differences = {
        "raw_minus_prevalence": {
            metric: metrics["raw_v45_oof"][metric] - metrics["constant_prevalence_oof"][metric]
            for metric in MODULE.PROBABILITY_METRICS
        },
        "platt_minus_prevalence": {
            metric: metrics["platt_oof"][metric] - metrics["constant_prevalence_oof"][metric]
            for metric in MODULE.PROBABILITY_METRICS
        },
    }
    endpoints = {}
    for index, key in enumerate(MODULE.REQUIRED_ENDPOINTS):
        bootstrap = {
            "unit": "patient_id cluster; repeated ECGs sampled together",
            "method": "paired unstratified percentile bootstrap on pooled out-of-fold scores",
            "replicates": 10,
            "seed": 197823 + index,
            "scope_limit": "conditional on the fitted fold-specific Platt and prevalence estimates",
            "comparisons": {
                comparison: {
                    metric: {
                        "valid_replicates": 10,
                        "invalid_replicates": 0,
                        "point_difference_first_minus_second": delta[metric],
                        "ci95": [delta[metric], delta[metric]],
                    }
                    for metric in MODULE.BOOTSTRAP_METRICS
                }
                for comparison, delta in differences.items()
            },
        }
        endpoints[key] = {
            "source_support": {
                "records": 10,
                "patients": 8,
                "positive_records": 2,
                "negative_records": 8,
                "positive_patients": 2,
            },
            "metrics": metrics,
            "point_differences": differences,
            "patient_cluster_bootstrap_deltas": bootstrap,
            "fold_support": [
                {
                    "fold": fold,
                    "fit_support": {
                        "records": 4,
                        "patients": 4,
                        "positive_records": 1,
                        "negative_records": 3,
                        "positive_patients": 1,
                    },
                    "evaluation_support": {
                        "records": 2,
                        "patients": patient_count,
                        "positive_records": positive_count,
                        "negative_records": 2 - positive_count,
                        "positive_patients": positive_count,
                    },
                    "fit_prevalence": 0.25,
                    "fit_test_patient_overlap": 0,
                }
                for fold, (patient_count, positive_count) in enumerate(
                    [(2, 1), (2, 0), (1, 1), (2, 0), (1, 0)]
                )
            ],
        }
    report = {
        "schema": "TITAN_V46_SPH_B1_PREVALENCE_COMPARISON_V1",
        "scope": "Supplementary exploratory analysis of previously observed SPH predictions.",
        "source": {
            "records": 10,
            "patients": 8,
            "reference": "presence of the frozen primary ECG statement code; absence is not adjudicated disease absence",
        },
        "design": {
            "outer_folds": 5,
            "seed": 197802,
            "patient_assignment_uses_labels": False,
            "fit_evaluation_patient_overlap": 0,
            "prevalence_estimator": config["prevalence_estimator"],
            "fit_partition_matches_platt": True,
            "constant_baseline_has_no_fitted_threshold": True,
            "metrics": list(MODULE.PROBABILITY_METRICS),
            "bootstrap_metrics": list(MODULE.BOOTSTRAP_METRICS),
            "all_sph_previously_observed": True,
            "confirmatory_external_test": False,
        },
        "input_sha256": config["input_sha256"],
        "source_b1_config_sha256": config["source_b1_config_sha256"],
        "source_b1_result_sha256": config["source_b1_result_sha256"],
        "source_b1_runner_sha256": config["source_b1_runner_sha256"],
        "protocol_sha256": config["protocol_sha256"],
        "individual_identifiers_exported": False,
        "record_level_scores_exported": False,
        "raw_signals_exported": False,
        "endpoints": endpoints,
        "execution": {
            "commit": "c" * 40,
            "slurm_job_id": "32762",
            "script_sha256": script_sha,
            "config_sha256": config_sha,
            "runtime": {
                "environment": config["runtime"]["environment"],
                "versions": config["runtime"]["versions"],
            },
        },
    }
    return report, config, config_sha, script_sha


def test_verifier_accepts_aggregate_when_hashes_counts_and_metrics_reconcile():
    report, config, config_sha, script_sha = _valid_fixture()

    result = MODULE.verify_aggregate(
        report,
        config,
        expected_job_id="32762",
        config_sha256=config_sha,
        script_sha256=script_sha,
    )

    assert result["endpoints"] == 6


def test_verifier_rejects_any_record_level_identifier_field():
    report, config, config_sha, script_sha = _valid_fixture()
    report["endpoints"]["P8:PAC"]["patient_id"] = "private-id"

    with pytest.raises(ValueError, match="private row-level key"):
        MODULE.verify_aggregate(
            report,
            config,
            expected_job_id="32762",
            config_sha256=config_sha,
            script_sha256=script_sha,
        )
