from __future__ import annotations

import hashlib
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
    config["bootstrap"]["scope_limit"] = (
        "conditional on fixed fold-specific Platt and prevalence estimates"
    )
    config["endpoints"] = [
        {"name": "P4:ASMI", "reference": "ASMI reference"},
        {"name": "P4:IMI", "reference": "IMI reference"},
        {"name": "P4:LVH", "reference": "LVH reference"},
        {"name": "P8:PAC", "reference": "PAC reference"},
        {"name": "P6:PVC", "reference": "PVC reference"},
        {"name": "P6:RBBB", "reference": "RBBB reference"},
    ]
    config_sha = "a" * 64
    runner_sha = "b" * 64
    verifier_sha = "d" * 64
    config["runner_sha256"] = runner_sha
    config["verifier_sha256"] = verifier_sha
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
            "scope_limit": config["bootstrap"]["scope_limit"],
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
            "reference": config["endpoints"][index]["reference"],
            "source_support": {
                "records": 10,
                "patients": 8,
                "positive_records": 5,
                "negative_records": 5,
                "positive_patients": 5,
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
                        "positive_records": 1,
                        "negative_records": 1,
                        "positive_patients": 1,
                    },
                    "fit_prevalence": 0.25,
                    "fit_test_patient_overlap": 0,
                }
                for fold, patient_count in enumerate([2, 2, 1, 2, 1])
            ],
        }
    report = {
        "schema": "TITAN_V46_SPH_B1_PREVALENCE_COMPARISON_V1",
        "scope": (
            "Supplementary exploratory analysis of previously observed SPH predictions; "
            "not an independent, locked, confirmatory, or clinical validation."
        ),
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
            "runner_sha256": runner_sha,
            "verifier_sha256": verifier_sha,
            "config_sha256": config_sha,
            "runtime": {
                "environment": config["runtime"]["environment"],
                "versions": config["runtime"]["versions"],
            },
        },
    }
    registry_entry = {
        "id": "B1-V46-SPH-PREVALENCE-COMPARATOR",
        "status": "completed_aggregate_only_exploratory",
        "configuration_sha256": config_sha,
        "runner_sha256": runner_sha,
        "verifier_sha256": verifier_sha,
        "protocol_sha256": config["protocol_sha256"],
        "cedia_job": 32762,
        "execution_commit": "c" * 40,
    }
    registry_entry["aggregate_sha256"] = _aggregate_sha256(report)
    return report, config, registry_entry, config_sha, runner_sha, verifier_sha


def _aggregate_sha256(report):
    payload = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def test_verifier_accepts_aggregate_when_hashes_counts_and_metrics_reconcile():
    report, config, registry, config_sha, runner_sha, verifier_sha = _valid_fixture()

    result = MODULE.verify_aggregate(
        report,
        config,
        registry_entry=registry,
        expected_job_id="32762",
        aggregate_sha256=registry["aggregate_sha256"],
        config_sha256=config_sha,
        runner_sha256=runner_sha,
        verifier_sha256=verifier_sha,
    )

    assert result["endpoints"] == 6


def test_verifier_rejects_any_record_level_identifier_field():
    report, config, registry, config_sha, runner_sha, verifier_sha = _valid_fixture()
    report["endpoints"]["P8:PAC"]["patient_ids"] = ["private-id"]
    registry["aggregate_sha256"] = _aggregate_sha256(report)

    with pytest.raises(ValueError, match="unrecognized key"):
        MODULE.verify_aggregate(
            report,
            config,
            registry_entry=registry,
            expected_job_id="32762",
            aggregate_sha256=_aggregate_sha256(report),
            config_sha256=config_sha,
            runner_sha256=runner_sha,
            verifier_sha256=verifier_sha,
        )


@pytest.mark.parametrize(
    ("path", "key", "value"),
    [
        (("endpoints", "P8:PAC"), "debug_records", [{"x": 1}]),
        (("endpoints", "P8:PAC", "source_support"), "patient_identifiers", ["x"]),
        ((), "patient_ids", ["x"]),
    ],
)
def test_verifier_rejects_unknown_private_payloads_at_every_depth(path, key, value):
    report, config, registry, config_sha, runner_sha, verifier_sha = _valid_fixture()
    target = report
    for part in path:
        target = target[part]
    target[key] = value
    registry["aggregate_sha256"] = _aggregate_sha256(report)

    with pytest.raises(ValueError, match="unrecognized key"):
        MODULE.verify_aggregate(
            report,
            config,
            registry_entry=registry,
            expected_job_id="32762",
            aggregate_sha256=_aggregate_sha256(report),
            config_sha256=config_sha,
            runner_sha256=runner_sha,
            verifier_sha256=verifier_sha,
        )


@pytest.mark.parametrize(
    ("support_path", "key", "value"),
    [
        (("source_support",), "negative_records", -1),
        (("source_support",), "positive_records", 11),
        (("source_support",), "positive_patients", 9),
        (("fold_support", 0, "fit_support"), "negative_records", -1),
        (("fold_support", 0, "evaluation_support"), "positive_patients", 3),
        (("fold_support", 0, "evaluation_support"), "patients", 3),
    ],
)
def test_verifier_rejects_impossible_support_counts(support_path, key, value):
    report, config, registry, config_sha, runner_sha, verifier_sha = _valid_fixture()
    target = report["endpoints"]["P8:PAC"]
    for part in support_path:
        target = target[part]
    target[key] = value
    registry["aggregate_sha256"] = _aggregate_sha256(report)

    with pytest.raises(ValueError, match="support|denominator|patient|class"):
        MODULE.verify_aggregate(
            report,
            config,
            registry_entry=registry,
            expected_job_id="32762",
            aggregate_sha256=_aggregate_sha256(report),
            config_sha256=config_sha,
            runner_sha256=runner_sha,
            verifier_sha256=verifier_sha,
        )


def test_verifier_rejects_runner_hash_not_pinned_by_registry():
    report, config, registry, config_sha, runner_sha, verifier_sha = _valid_fixture()
    registry["runner_sha256"] = "e" * 64

    with pytest.raises(ValueError, match="registry.*runner|runner.*registry"):
        MODULE.verify_aggregate(
            report,
            config,
            registry_entry=registry,
            expected_job_id="32762",
            aggregate_sha256=registry["aggregate_sha256"],
            config_sha256=config_sha,
            runner_sha256=runner_sha,
            verifier_sha256=verifier_sha,
        )


@pytest.mark.parametrize(
    ("field", "actual_hash"),
    [("runner_sha256", "e" * 64), ("verifier_sha256", "e" * 64)],
)
def test_verifier_rejects_code_hash_drift_in_frozen_configuration(field, actual_hash):
    report, config, registry, config_sha, runner_sha, verifier_sha = _valid_fixture()
    config[field] = actual_hash

    with pytest.raises(ValueError, match="differs from frozen config"):
        MODULE.verify_aggregate(
            report,
            config,
            registry_entry=registry,
            expected_job_id="32762",
            aggregate_sha256=registry["aggregate_sha256"],
            config_sha256=config_sha,
            runner_sha256=runner_sha,
            verifier_sha256=verifier_sha,
        )


def test_verifier_rejects_aggregate_hash_not_pinned_by_registry():
    report, config, registry, config_sha, runner_sha, verifier_sha = _valid_fixture()
    registry["aggregate_sha256"] = "e" * 64

    with pytest.raises(ValueError, match="registry aggregate hash"):
        MODULE.verify_aggregate(
            report,
            config,
            registry_entry=registry,
            expected_job_id="32762",
            aggregate_sha256=_aggregate_sha256(report),
            config_sha256=config_sha,
            runner_sha256=runner_sha,
            verifier_sha256=verifier_sha,
        )


def test_verifier_rejects_execution_commit_not_frozen_in_registry():
    report, config, registry, config_sha, runner_sha, verifier_sha = _valid_fixture()
    registry["execution_commit"] = "e" * 40

    with pytest.raises(ValueError, match="execution commit"):
        MODULE.verify_aggregate(
            report,
            config,
            registry_entry=registry,
            expected_job_id="32762",
            aggregate_sha256=registry["aggregate_sha256"],
            config_sha256=config_sha,
            runner_sha256=runner_sha,
            verifier_sha256=verifier_sha,
        )


def test_verifier_rejects_execution_job_not_frozen_in_registry():
    report, config, registry, config_sha, runner_sha, verifier_sha = _valid_fixture()
    registry["cedia_job"] = 99999

    with pytest.raises(ValueError, match="registry CEDIA job"):
        MODULE.verify_aggregate(
            report,
            config,
            registry_entry=registry,
            expected_job_id="32762",
            aggregate_sha256=registry["aggregate_sha256"],
            config_sha256=config_sha,
            runner_sha256=runner_sha,
            verifier_sha256=verifier_sha,
        )
