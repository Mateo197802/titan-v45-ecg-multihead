"""Validate the public, aggregate-only receipt from the B1 SPH diagnostic."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path

METRICS = (
    "accuracy",
    "sensitivity",
    "specificity",
    "ppv",
    "npv",
    "f1",
    "auroc",
    "average_precision",
    "brier",
    "ece",
)
CONFUSION = ("tp", "fp", "tn", "fn")
DECISION_REPORTS = (
    "v45_frozen_baseline",
    "raw_nested_cv",
    "platt_nested_cv",
    "platt_at_0_5_reference_operating_point",
)
FORBIDDEN_KEY_PARTS = (
    "record_id",
    "record_ids",
    "ecg_id",
    "patient_id",
    "patient_ids",
    "raw_signal",
    "record_level_prediction",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _fail(message: str) -> None:
    raise ValueError(message)


def _walk_for_private_keys(value: object) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            if any(part in normalized for part in FORBIDDEN_KEY_PARTS):
                _fail("aggregate contains a patient-level or record-level field")
            _walk_for_private_keys(child)
    elif isinstance(value, list):
        for child in value:
            _walk_for_private_keys(child)


def _check_count(value: object, name: str, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        _fail(f"{name} must be an integer >= {minimum}")
    return value


def _check_metrics(metrics: dict, expected_records: int, name: str) -> None:
    if _check_count(metrics.get("records"), f"{name}.records") != expected_records:
        _fail(f"{name} record denominator differs from the frozen cohort")
    confusion = metrics.get("confusion")
    if not isinstance(confusion, dict) or set(confusion) != set(CONFUSION):
        _fail(f"{name} confusion matrix is malformed")
    confusion_total = sum(_check_count(confusion.get(key), f"{name}.confusion.{key}") for key in CONFUSION)
    if confusion_total != expected_records:
        _fail(f"{name} confusion denominator does not match records")
    tp, fp, tn, fn = (confusion[key] for key in CONFUSION)
    positive = _check_count(metrics.get("positive_support"), f"{name}.positive_support")
    negative = _check_count(metrics.get("negative_support"), f"{name}.negative_support")
    predicted_positive = _check_count(
        metrics.get("predicted_positive_support"), f"{name}.predicted_positive_support"
    )
    if positive != tp + fn or negative != tn + fp or positive + negative != expected_records:
        _fail(f"{name} confusion and reference supports do not reconcile")
    if predicted_positive != tp + fp:
        _fail(f"{name} predicted-positive support does not reconcile with confusion")

    def ratio(numerator: int, denominator: int) -> float | None:
        return None if denominator == 0 else numerator / denominator

    derived_metrics = {
        "accuracy": ratio(tp + tn, expected_records),
        "sensitivity": ratio(tp, tp + fn),
        "specificity": ratio(tn, tn + fp),
        "ppv": ratio(tp, tp + fp),
        "npv": ratio(tn, tn + fn),
        "f1": ratio(2 * tp, 2 * tp + fp + fn),
    }
    for metric in METRICS:
        value = metrics.get(metric)
        if value is not None and (
            not isinstance(value, (int, float))
            or not math.isfinite(value)
            or not 0.0 <= value <= 1.0
        ):
            _fail(f"{name}.{metric} must be null or a finite value in [0, 1]")
    for metric, expected in derived_metrics.items():
        actual = metrics.get(metric)
        if expected is None:
            if actual is not None:
                _fail(f"{name}.{metric} does not reconcile with confusion")
        elif actual is None or not math.isclose(
            actual, expected, rel_tol=1e-9, abs_tol=1e-12
        ):
            _fail(f"{name}.{metric} does not reconcile with confusion")


def _check_fold_support(
    fold_support: object, expected_records: int, expected_patients: int
) -> None:
    if not isinstance(fold_support, list) or len(fold_support) != 5:
        _fail("fold support must contain all five frozen outer folds")
    for fold_index, fold in enumerate(fold_support):
        if not isinstance(fold, dict) or set(fold) != {"fit", "threshold_tune", "test"}:
            _fail(f"fold {fold_index} has malformed patient partitions")
        record_total = 0
        patient_total = 0
        for role, support in fold.items():
            if not isinstance(support, dict):
                _fail(f"fold {fold_index} {role} support is malformed")
            records = _check_count(support.get("records"), f"fold {fold_index} {role}.records")
            patients = _check_count(support.get("patients"), f"fold {fold_index} {role}.patients")
            positive = _check_count(
                support.get("positive_records"), f"fold {fold_index} {role}.positive_records"
            )
            positive_patients = _check_count(
                support.get("positive_patients"),
                f"fold {fold_index} {role}.positive_patients",
            )
            negative = _check_count(
                support.get("negative_records"), f"fold {fold_index} {role}.negative_records"
            )
            if positive + negative != records:
                _fail(f"fold {fold_index} {role} class supports do not match records")
            if positive_patients > patients or positive_patients > positive:
                _fail(f"fold {fold_index} {role} positive patients exceed partition support")
            record_total += records
            patient_total += patients
        if record_total != expected_records or patient_total != expected_patients:
            _fail(f"fold {fold_index} partition denominators do not reconcile")


def verify_aggregate_report(
    report_path: Path,
    config_path: Path,
    calibrator_path: Path,
    *,
    expected_job_id: str | None = None,
) -> dict:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if report.get("schema") != "TITAN_V46_SPH_B1_CALIBRATION_DIAGNOSTIC_V1":
        _fail("unexpected B1 result schema")
    _walk_for_private_keys(report)
    if report.get("individual_identifiers_exported") is not False:
        _fail("individual identifier privacy flag must be false")
    if report.get("record_level_outputs_exported") is not False:
        _fail("record-level output privacy flag must be false")

    expected_records = _check_count(config.get("expected_records"), "config.expected_records", minimum=1)
    expected_patients = _check_count(config["source"].get("patients"), "config.source.patients", minimum=1)
    source = report.get("source", {})
    if source.get("records") != expected_records or source.get("patients") != expected_patients:
        _fail("aggregate source population differs from frozen configuration")
    if report.get("input_sha256") != config.get("input_sha256"):
        _fail("aggregate input hashes differ from frozen configuration")
    if report.get("source_v45_protocol_commit") != config["source"].get("v45_protocol_commit"):
        _fail("aggregate does not identify the frozen V4.5 protocol commit")

    design = report.get("design", {})
    if design.get("all_spH_already_observed") is not True:
        _fail("SPH prior observation must remain disclosed")
    if design.get("confirmatory_external_test") is not False:
        _fail("SPH must not be described as confirmatory external testing")
    if design.get("fit_tune_test_patient_overlap") != 0:
        _fail("fit, tune, and evaluation patient partitions must be disjoint")

    expected_endpoints = {
        f"{item['profile']}:{item['name']}" for item in config.get("endpoints", [])
    }
    endpoints = report.get("endpoints")
    if not isinstance(endpoints, dict) or set(endpoints) != expected_endpoints:
        _fail("aggregate endpoint set differs from the frozen configuration")
    bootstrap_config = config["metrics"]["bootstrap"]
    if tuple(bootstrap_config.get("delta_metrics", ())) != METRICS:
        _fail("frozen bootstrap metric set differs from the verifier contract")
    expected_replicates = _check_count(
        bootstrap_config.get("replicates"), "config.metrics.bootstrap.replicates", minimum=1
    )

    for endpoint_name, endpoint in endpoints.items():
        support = endpoint.get("source_support", {})
        if support.get("records") != expected_records or support.get("patients") != expected_patients:
            _fail(f"{endpoint_name} source denominator differs from the frozen cohort")
        if support.get("positive_records", -1) + support.get("negative_records", -1) != expected_records:
            _fail(f"{endpoint_name} source class supports do not match records")
        for report_name in DECISION_REPORTS:
            result = endpoint.get(report_name, {})
            _check_metrics(result.get("metrics", {}), expected_records, f"{endpoint_name}.{report_name}")
        _check_fold_support(endpoint.get("fold_support"), expected_records, expected_patients)

        bootstrap = endpoint.get("paired_patient_cluster_bootstrap_delta", {})
        if bootstrap.get("replicates") != expected_replicates:
            _fail(f"{endpoint_name} bootstrap replicate count differs from configuration")
        intervals = bootstrap.get("intervals")
        if not isinstance(intervals, dict) or set(intervals) != set(METRICS):
            _fail(f"{endpoint_name} bootstrap metric set is incomplete")
        for metric, interval in intervals.items():
            valid = _check_count(interval.get("valid_replicates"), f"{endpoint_name}.{metric}.valid_replicates")
            invalid = _check_count(interval.get("invalid_replicates"), f"{endpoint_name}.{metric}.invalid_replicates")
            if valid + invalid != expected_replicates:
                _fail(f"{endpoint_name}.{metric} bootstrap counts do not reconcile")
            raw_value = endpoint["raw_nested_cv"]["metrics"].get(metric)
            calibrated_value = endpoint["platt_nested_cv"]["metrics"].get(metric)
            expected_delta = (
                None
                if raw_value is None or calibrated_value is None
                else calibrated_value - raw_value
            )
            point_delta = interval.get("point_difference_calibrated_minus_raw")
            if expected_delta is None:
                if point_delta is not None:
                    _fail(f"{endpoint_name}.{metric} bootstrap point difference does not reconcile")
            elif (
                not isinstance(point_delta, (int, float))
                or not math.isfinite(point_delta)
                or not math.isclose(
                    point_delta, expected_delta, rel_tol=1e-9, abs_tol=1e-12
                )
            ):
                _fail(f"{endpoint_name}.{metric} bootstrap point difference does not reconcile")
            ci = interval.get("ci95")
            if ci is None:
                if valid != 0:
                    _fail(f"{endpoint_name}.{metric} has valid replicates but no interval")
            elif (
                valid == 0
                or not isinstance(ci, list)
                or len(ci) != 2
                or any(not isinstance(value, (int, float)) or not math.isfinite(value) for value in ci)
                or ci[0] > ci[1]
                or ci[0] < -1.0
                or ci[1] > 1.0
            ):
                _fail(f"{endpoint_name}.{metric} bootstrap interval is malformed")

    execution = report.get("execution", {})
    if not isinstance(execution.get("commit"), str) or not re.fullmatch(r"[0-9a-f]{40}", execution["commit"]):
        _fail("execution commit must be a full lowercase Git object ID")
    if expected_job_id is not None and str(execution.get("slurm_job_id")) != expected_job_id:
        _fail("SLURM job ID differs from the expected execution")
    if execution.get("script_sha256") != sha256_file(calibrator_path):
        _fail("aggregate calibrator hash differs from the current script")
    if execution.get("b1_config_sha256") != sha256_file(config_path):
        _fail("aggregate B1 configuration hash differs from the current config")
    if execution.get("runtime") != config.get("runtime"):
        _fail("aggregate runtime differs from the frozen environment")

    return {
        "schema": report["schema"],
        "records": expected_records,
        "patients": expected_patients,
        "endpoints": sorted(expected_endpoints),
        "slurm_job_id": str(execution["slurm_job_id"]),
        "report_sha256": sha256_file(report_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--calibrator", type=Path, required=True)
    parser.add_argument("--expected-job-id")
    args = parser.parse_args()
    result = verify_aggregate_report(
        args.report,
        args.config,
        args.calibrator,
        expected_job_id=args.expected_job_id,
    )
    print(
        "Verified aggregate-only B1 result: "
        f"job={result['slurm_job_id']} records={result['records']} "
        f"patients={result['patients']} endpoints={len(result['endpoints'])} "
        f"sha256={result['report_sha256']}"
    )


if __name__ == "__main__":
    main()
