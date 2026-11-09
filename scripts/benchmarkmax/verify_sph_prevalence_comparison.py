"""Verify the aggregate-only receipt for the SPH prevalence comparator."""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/benchmarkmax"))
from compare_sph_prevalence_baseline import (
    BOOTSTRAP_METRICS,
    COMPARISONS,
    PROBABILITY_METRICS,
    sha256_file,
)

REQUIRED_ENDPOINTS = (
    "P4:ASMI",
    "P4:IMI",
    "P4:LVH",
    "P6:PVC",
    "P6:RBBB",
    "P8:PAC",
)
FORBIDDEN_KEYS = {
    "ecg_id",
    "record_id",
    "patient_id",
    "signal",
    "waveform",
    "row_predictions",
    "per_record_scores",
}


def _reject_private_keys(value) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key.lower() in FORBIDDEN_KEYS:
                raise ValueError(f"aggregate contains private row-level key: {key}")
            _reject_private_keys(item)
    elif isinstance(value, list):
        for item in value:
            _reject_private_keys(item)


def _finite_metric(value, name: str) -> float:
    if not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"metric {name} must be finite")
    return float(value)


def verify_aggregate(
    report: dict,
    config: dict,
    *,
    expected_job_id: str,
    config_sha256: str,
    script_sha256: str,
) -> dict:
    _reject_private_keys(report)
    if report.get("schema") != "TITAN_V46_SPH_B1_PREVALENCE_COMPARISON_V1":
        raise ValueError("unexpected prevalence comparison schema")
    if "previously observed SPH" not in report.get("scope", ""):
        raise ValueError("aggregate scope must disclose previously observed SPH")
    if report.get("source") != {
        "records": config["source"]["records"],
        "patients": config["source"]["patients"],
        "reference": "presence of the frozen primary ECG statement code; absence is not adjudicated disease absence",
    }:
        raise ValueError("aggregate source population or reference differs from frozen configuration")

    design = report.get("design", {})
    if (
        design.get("outer_folds") != config["source"]["b1_outer_folds"]
        or design.get("seed") != config["source"]["b1_protocol_seed"]
        or design.get("patient_assignment_uses_labels") is not False
        or design.get("fit_evaluation_patient_overlap") != 0
        or design.get("fit_partition_matches_platt") is not True
        or design.get("constant_baseline_has_no_fitted_threshold") is not True
        or design.get("all_sph_previously_observed") is not True
        or design.get("confirmatory_external_test") is not False
        or design.get("prevalence_estimator") != config["prevalence_estimator"]
        or design.get("metrics") != list(PROBABILITY_METRICS)
        or design.get("bootstrap_metrics") != list(BOOTSTRAP_METRICS)
    ):
        raise ValueError("analysis design differs from the frozen prevalence comparator protocol")

    if report.get("input_sha256") != config["input_sha256"]:
        raise ValueError("aggregate frozen input hashes differ")
    for key, config_key in (
        ("source_b1_config_sha256", "source_b1_config_sha256"),
        ("source_b1_result_sha256", "source_b1_result_sha256"),
        ("source_b1_runner_sha256", "source_b1_runner_sha256"),
        ("protocol_sha256", "protocol_sha256"),
    ):
        if report.get(key) != config[config_key]:
            raise ValueError(f"aggregate {key} differs from frozen configuration")

    for flag in (
        "individual_identifiers_exported",
        "record_level_scores_exported",
        "raw_signals_exported",
    ):
        if report.get(flag) is not False:
            raise ValueError(f"privacy flag {flag} must be false")

    execution = report.get("execution", {})
    if execution.get("slurm_job_id") != str(expected_job_id):
        raise ValueError("aggregate SLURM job ID differs from the expected job")
    if execution.get("script_sha256") != script_sha256:
        raise ValueError("aggregate runner hash differs from current source")
    if execution.get("config_sha256") != config_sha256:
        raise ValueError("aggregate configuration hash differs from current config")
    if execution.get("runtime", {}).get("versions") != config["runtime"]["versions"]:
        raise ValueError("aggregate runtime differs from frozen configuration")
    if not isinstance(execution.get("commit"), str) or len(execution["commit"]) != 40:
        raise ValueError("aggregate execution commit is invalid")

    endpoints = report.get("endpoints", {})
    if set(endpoints) != set(REQUIRED_ENDPOINTS):
        raise ValueError("aggregate endpoint set differs from frozen B1 targets")
    expected_records = int(config["source"]["records"])
    expected_patients = int(config["source"]["patients"])
    expected_replicates = int(config["bootstrap"]["replicates"])
    expected_seed = int(config["bootstrap"]["base_seed"])

    for endpoint_index, endpoint_name in enumerate(REQUIRED_ENDPOINTS):
        endpoint = endpoints[endpoint_name]
        support = endpoint.get("source_support", {})
        if (
            support.get("records") != expected_records
            or support.get("patients") != expected_patients
            or support.get("positive_records", -1) + support.get("negative_records", -1)
            != expected_records
            or not 0 <= support.get("positive_patients", -1) <= expected_patients
        ):
            raise ValueError(f"source denominator is inconsistent for {endpoint_name}")

        metrics = endpoint.get("metrics", {})
        if set(metrics) != {"raw_v45_oof", "platt_oof", "constant_prevalence_oof"}:
            raise ValueError(f"probability methods are incomplete for {endpoint_name}")
        for method, method_metrics in metrics.items():
            if set(method_metrics) != set(PROBABILITY_METRICS):
                raise ValueError(f"probability metrics are incomplete for {endpoint_name} {method}")
            for metric in PROBABILITY_METRICS:
                value = _finite_metric(method_metrics[metric], metric)
                if metric == "log_loss" and value < 0:
                    raise ValueError("log-loss cannot be negative")
                if metric != "log_loss" and not 0 <= value <= 1:
                    raise ValueError(f"metric {metric} must be in [0, 1]")

        differences = endpoint.get("point_differences", {})
        if set(differences) != set(COMPARISONS):
            raise ValueError(f"point comparisons are incomplete for {endpoint_name}")
        for comparison, (first, second) in COMPARISONS.items():
            if set(differences[comparison]) != set(PROBABILITY_METRICS):
                raise ValueError(f"point difference metrics are incomplete for {endpoint_name}")
            for metric, difference in differences[comparison].items():
                expected_difference = metrics[first][metric] - metrics[second][metric]
                if not math.isclose(
                    _finite_metric(difference, metric), expected_difference, rel_tol=0.0, abs_tol=1e-12
                ):
                    raise ValueError(f"point difference does not reconcile for {endpoint_name} {metric}")

        folds = endpoint.get("fold_support", [])
        if len(folds) != int(config["source"]["b1_outer_folds"]):
            raise ValueError(f"fold support is incomplete for {endpoint_name}")
        if [item.get("fold") for item in folds] != list(range(len(folds))):
            raise ValueError(f"fold identifiers are invalid for {endpoint_name}")
        if sum(item["evaluation_support"]["records"] for item in folds) != expected_records:
            raise ValueError(f"outer-fold record denominator does not reconcile for {endpoint_name}")
        if sum(item["evaluation_support"]["patients"] for item in folds) != expected_patients:
            raise ValueError(f"outer-fold patient denominator does not reconcile for {endpoint_name}")
        if sum(item["evaluation_support"]["positive_records"] for item in folds) != support["positive_records"]:
            raise ValueError(f"outer-fold positive record support does not reconcile for {endpoint_name}")
        if sum(item["evaluation_support"]["negative_records"] for item in folds) != support["negative_records"]:
            raise ValueError(f"outer-fold negative record support does not reconcile for {endpoint_name}")
        if sum(item["evaluation_support"]["positive_patients"] for item in folds) != support["positive_patients"]:
            raise ValueError(f"outer-fold positive-patient support does not reconcile for {endpoint_name}")
        if any(item.get("fit_test_patient_overlap") != 0 for item in folds):
            raise ValueError(f"fit and outer-evaluation patients overlap for {endpoint_name}")
        for item in folds:
            fit_support = item["fit_support"]
            if (
                fit_support["records"] <= 0
                or fit_support["patients"] <= 0
                or fit_support["positive_records"] + fit_support["negative_records"]
                != fit_support["records"]
                or not math.isclose(
                    item["fit_prevalence"],
                    fit_support["positive_records"] / fit_support["records"],
                    rel_tol=0.0,
                    abs_tol=1e-12,
                )
            ):
                raise ValueError(f"fold prevalence does not reconcile with fit support for {endpoint_name}")

        bootstrap = endpoint.get("patient_cluster_bootstrap_deltas", {})
        if (
            bootstrap.get("replicates") != expected_replicates
            or bootstrap.get("seed") != expected_seed + endpoint_index
            or bootstrap.get("unit") != "patient_id cluster; repeated ECGs sampled together"
            or set(bootstrap.get("comparisons", {})) != set(COMPARISONS)
        ):
            raise ValueError(f"bootstrap protocol differs for {endpoint_name}")
        for comparison, metrics_ci in bootstrap["comparisons"].items():
            if set(metrics_ci) != set(BOOTSTRAP_METRICS):
                raise ValueError(f"bootstrap metrics differ for {endpoint_name} {comparison}")
            for metric, result in metrics_ci.items():
                if (
                    result.get("valid_replicates") != expected_replicates
                    or result.get("invalid_replicates") != 0
                ):
                    raise ValueError(f"bootstrap replicate accounting fails for {endpoint_name} {metric}")
                interval = result.get("ci95")
                if not isinstance(interval, list) or len(interval) != 2:
                    raise ValueError(f"bootstrap interval is missing for {endpoint_name} {metric}")
                lower, upper = (_finite_metric(item, metric) for item in interval)
                if lower > upper:
                    raise ValueError(f"bootstrap interval is reversed for {endpoint_name} {metric}")
                point = _finite_metric(result.get("point_difference_first_minus_second"), metric)
                if not math.isclose(
                    point,
                    differences[comparison][metric],
                    rel_tol=0.0,
                    abs_tol=1e-12,
                ):
                    raise ValueError(f"bootstrap point estimate differs for {endpoint_name} {metric}")

    return {
        "schema": report["schema"],
        "job_id": str(expected_job_id),
        "records": expected_records,
        "patients": expected_patients,
        "endpoints": len(endpoints),
        "aggregate_only": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--runner", type=Path, required=True)
    parser.add_argument("--expected-job-id", required=True)
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    config = json.loads(args.config.read_text(encoding="utf-8"))
    result = verify_aggregate(
        report,
        config,
        expected_job_id=args.expected_job_id,
        config_sha256=sha256_file(args.config),
        script_sha256=sha256_file(args.runner),
    )
    print(
        "Verified aggregate-only SPH prevalence comparison: "
        f"job {result['job_id']}, {result['records']} records, "
        f"{result['patients']} patients, {result['endpoints']} endpoints"
    )


if __name__ == "__main__":
    main()
