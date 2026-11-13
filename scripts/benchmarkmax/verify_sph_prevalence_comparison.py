"""Verify the aggregate-only receipt for the SPH prevalence comparator."""
from __future__ import annotations

import argparse
import json
import math
import re
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
    "P8:PAC",
    "P6:PVC",
    "P6:RBBB",
)
SUPPORT_KEYS = {"records", "patients", "positive_records", "negative_records", "positive_patients"}
METHODS = {"raw_v45_oof", "platt_oof", "constant_prevalence_oof"}
REPORT_KEYS = {
    "schema", "scope", "source", "design", "input_sha256", "source_b1_config_sha256",
    "source_b1_result_sha256", "source_b1_runner_sha256", "protocol_sha256",
    "individual_identifiers_exported", "record_level_scores_exported", "raw_signals_exported",
    "endpoints", "execution",
}
DESIGN_KEYS = {
    "outer_folds", "seed", "patient_assignment_uses_labels", "fit_evaluation_patient_overlap",
    "prevalence_estimator", "fit_partition_matches_platt", "constant_baseline_has_no_fitted_threshold",
    "metrics", "bootstrap_metrics", "all_sph_previously_observed", "confirmatory_external_test",
}
ENDPOINT_KEYS = {
    "reference", "source_support", "metrics", "point_differences",
    "patient_cluster_bootstrap_deltas", "fold_support",
}
EXECUTION_KEYS = {
    "commit", "slurm_job_id", "runner_sha256", "verifier_sha256", "config_sha256", "runtime",
}
FORBIDDEN_KEYS = {
    "ecg_id", "ecg_ids", "record_id", "record_ids", "patient_id", "patient_ids", "signal",
    "signals", "waveform", "waveforms", "row_predictions", "per_record_scores", "debug_records",
}


def _assert_exact_keys(value: object, expected: set[str], label: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    actual = set(value)
    unknown = actual - expected
    missing = expected - actual
    if unknown:
        raise ValueError(f"aggregate contains unrecognized key(s) in {label}: {sorted(unknown)}")
    if missing:
        raise ValueError(f"aggregate is missing required key(s) in {label}: {sorted(missing)}")
    for key in actual:
        if key.lower() in FORBIDDEN_KEYS:
            raise ValueError(f"aggregate contains private row-level key: {key}")
    return value


def _finite_metric(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"metric {name} must be finite")
    return float(value)


def _nonnegative_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value


def _digest(value: object, name: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    return value


def _validate_support(value: object, label: str, *, require_both_classes: bool) -> dict:
    support = _assert_exact_keys(value, SUPPORT_KEYS, label)
    counts = {key: _nonnegative_int(support[key], f"{label}.{key}") for key in SUPPORT_KEYS}
    records, patients = counts["records"], counts["patients"]
    positive, negative, positive_patients = (
        counts["positive_records"], counts["negative_records"], counts["positive_patients"]
    )
    if records <= 0 or patients <= 0 or patients > records:
        raise ValueError(f"{label} has impossible record/patient support")
    if positive + negative != records:
        raise ValueError(f"{label} class support does not sum to its record denominator")
    if positive_patients > patients or positive_patients > positive:
        raise ValueError(f"{label} positive-patient support is impossible")
    if (positive == 0) != (positive_patients == 0):
        raise ValueError(f"{label} positive record and patient support disagree")
    if require_both_classes and (positive == 0 or negative == 0):
        raise ValueError(f"{label} requires support from both statement classes")
    return counts


def _validate_registry_anchor(
    registry_entry: dict,
    *,
    expected_job_id: str,
    aggregate_sha256: str,
    config: dict,
    config_sha256: str,
    runner_sha256: str,
    verifier_sha256: str,
    execution_commit: str,
) -> None:
    if registry_entry.get("id") != "B1-V46-SPH-PREVALENCE-COMPARATOR":
        raise ValueError("registry entry does not identify the prevalence comparator")
    if registry_entry.get("status") != "completed_aggregate_only_exploratory":
        raise ValueError("registry entry is not marked as a completed aggregate-only analysis")
    for registry_key, actual, label in (
        ("configuration_sha256", config_sha256, "configuration"),
        ("runner_sha256", runner_sha256, "runner"),
        ("verifier_sha256", verifier_sha256, "verifier"),
        ("protocol_sha256", config["protocol_sha256"], "protocol"),
        ("aggregate_sha256", aggregate_sha256, "aggregate"),
    ):
        expected = _digest(registry_entry.get(registry_key), f"registry {registry_key}")
        if expected != actual:
            raise ValueError(f"registry {label} hash does not match the verified artifact")
    if str(registry_entry.get("cedia_job")) != str(expected_job_id):
        raise ValueError("registry CEDIA job ID differs from the expected job")
    if registry_entry.get("execution_commit") != execution_commit:
        raise ValueError("execution commit differs from the frozen registry entry")


def verify_aggregate(
    report: dict,
    config: dict,
    *,
    registry_entry: dict,
    expected_job_id: str,
    aggregate_sha256: str,
    config_sha256: str,
    runner_sha256: str,
    verifier_sha256: str,
) -> dict:
    _assert_exact_keys(report, REPORT_KEYS, "report")
    if report.get("schema") != "TITAN_V46_SPH_B1_PREVALENCE_COMPARISON_V1":
        raise ValueError("unexpected prevalence comparison schema")
    if report.get("scope") != (
        "Supplementary exploratory analysis of previously observed SPH predictions; "
        "not an independent, locked, confirmatory, or clinical validation."
    ):
        raise ValueError("aggregate scope must disclose previously observed SPH")

    source = _assert_exact_keys(
        report["source"], {"records", "patients", "reference"}, "source"
    )
    source_records = _nonnegative_int(source["records"], "source.records")
    source_patients = _nonnegative_int(source["patients"], "source.patients")
    if (
        source_records != config["source"]["records"]
        or source_patients != config["source"]["patients"]
        or source["reference"]
        != "presence of the frozen primary ECG statement code; absence is not adjudicated disease absence"
    ):
        raise ValueError("aggregate source population or reference differs from frozen configuration")

    design = _assert_exact_keys(report["design"], DESIGN_KEYS, "design")
    if (
        design["outer_folds"] != config["source"]["b1_outer_folds"]
        or design["seed"] != config["source"]["b1_protocol_seed"]
        or design["patient_assignment_uses_labels"] is not False
        or design["fit_evaluation_patient_overlap"] != 0
        or design["fit_partition_matches_platt"] is not True
        or design["constant_baseline_has_no_fitted_threshold"] is not True
        or design["all_sph_previously_observed"] is not True
        or design["confirmatory_external_test"] is not False
        or design["prevalence_estimator"] != config["prevalence_estimator"]
        or design["metrics"] != list(PROBABILITY_METRICS)
        or design["bootstrap_metrics"] != list(BOOTSTRAP_METRICS)
    ):
        raise ValueError("analysis design differs from the frozen prevalence comparator protocol")

    input_hashes = _assert_exact_keys(
        report["input_sha256"], set(config["input_sha256"]), "input_sha256"
    )
    if input_hashes != config["input_sha256"]:
        raise ValueError("aggregate frozen input hashes differ")
    for key in (
        "source_b1_config_sha256", "source_b1_result_sha256", "source_b1_runner_sha256", "protocol_sha256"
    ):
        _digest(report[key], key)
        if report[key] != config[key]:
            raise ValueError(f"aggregate {key} differs from frozen configuration")

    for flag in (
        "individual_identifiers_exported", "record_level_scores_exported", "raw_signals_exported"
    ):
        if report[flag] is not False:
            raise ValueError(f"privacy flag {flag} must be false")

    execution = _assert_exact_keys(report["execution"], EXECUTION_KEYS, "execution")
    commit = execution["commit"]
    if not isinstance(commit, str) or re.fullmatch(r"[0-9a-f]{40}", commit) is None:
        raise ValueError("aggregate execution commit is invalid")
    if execution["slurm_job_id"] != str(expected_job_id):
        raise ValueError("aggregate SLURM job ID differs from the expected job")
    for name, actual in (("runner_sha256", runner_sha256), ("verifier_sha256", verifier_sha256)):
        if _digest(config.get(name), f"config {name}") != actual:
            raise ValueError(f"current {name.removesuffix('_sha256')} differs from frozen config")
        if _digest(execution[name], f"execution {name}") != actual:
            raise ValueError(f"aggregate {name.removesuffix('_sha256')} differs from current source")
    if _digest(config_sha256, "configuration hash") != _digest(
        execution["config_sha256"], "execution config hash"
    ):
        raise ValueError("aggregate configuration hash differs from current config")
    runtime = _assert_exact_keys(execution["runtime"], {"environment", "versions"}, "runtime")
    versions = _assert_exact_keys(
        runtime["versions"], set(config["runtime"]["versions"]), "runtime.versions"
    )
    if runtime["environment"] != config["runtime"]["environment"] or versions != config["runtime"]["versions"]:
        raise ValueError("aggregate runtime differs from frozen configuration")

    _validate_registry_anchor(
        registry_entry,
        expected_job_id=expected_job_id,
        aggregate_sha256=aggregate_sha256,
        config=config,
        config_sha256=config_sha256,
        runner_sha256=runner_sha256,
        verifier_sha256=verifier_sha256,
        execution_commit=commit,
    )

    endpoint_config = config["endpoints"]
    expected_endpoint_names = [item["name"] for item in endpoint_config]
    if tuple(expected_endpoint_names) != REQUIRED_ENDPOINTS:
        raise ValueError("frozen comparator endpoint order is invalid")
    endpoints = _assert_exact_keys(report["endpoints"], set(REQUIRED_ENDPOINTS), "endpoints")
    expected_records = int(config["source"]["records"])
    expected_patients = int(config["source"]["patients"])
    expected_replicates = int(config["bootstrap"]["replicates"])
    expected_seed = int(config["bootstrap"]["base_seed"])

    for endpoint_index, target in enumerate(endpoint_config):
        endpoint_name = target["name"]
        endpoint = _assert_exact_keys(endpoints[endpoint_name], ENDPOINT_KEYS, endpoint_name)
        if endpoint["reference"] != target["reference"]:
            raise ValueError(f"endpoint reference differs from frozen configuration for {endpoint_name}")

        support = _validate_support(
            endpoint["source_support"], f"{endpoint_name}.source_support", require_both_classes=True
        )
        if support["records"] != expected_records or support["patients"] != expected_patients:
            raise ValueError(f"source denominator is inconsistent for {endpoint_name}")

        metrics = _assert_exact_keys(endpoint["metrics"], METHODS, f"{endpoint_name}.metrics")
        for method, method_metrics in metrics.items():
            method_metrics = _assert_exact_keys(
                method_metrics, set(PROBABILITY_METRICS), f"{endpoint_name}.{method}"
            )
            for metric in PROBABILITY_METRICS:
                value = _finite_metric(method_metrics[metric], metric)
                if metric == "log_loss" and value < 0:
                    raise ValueError("log-loss cannot be negative")
                if metric != "log_loss" and not 0 <= value <= 1:
                    raise ValueError(f"metric {metric} must be in [0, 1]")

        differences = _assert_exact_keys(
            endpoint["point_differences"], set(COMPARISONS), f"{endpoint_name}.point_differences"
        )
        for comparison, (first, second) in COMPARISONS.items():
            values = _assert_exact_keys(
                differences[comparison], set(PROBABILITY_METRICS), f"{endpoint_name}.{comparison}"
            )
            for metric, difference in values.items():
                expected_difference = metrics[first][metric] - metrics[second][metric]
                if not math.isclose(
                    _finite_metric(difference, metric), expected_difference, rel_tol=0.0, abs_tol=1e-12
                ):
                    raise ValueError(f"point difference does not reconcile for {endpoint_name} {metric}")

        folds = endpoint["fold_support"]
        if not isinstance(folds, list) or len(folds) != int(config["source"]["b1_outer_folds"]):
            raise ValueError(f"fold support is incomplete for {endpoint_name}")
        fold_supports = []
        for fold_index, item in enumerate(folds):
            item = _assert_exact_keys(
                item,
                {"fold", "fit_support", "evaluation_support", "fit_prevalence", "fit_test_patient_overlap"},
                f"{endpoint_name}.fold_support[{fold_index}]",
            )
            if item["fold"] != fold_index:
                raise ValueError(f"fold identifiers are invalid for {endpoint_name}")
            fit = _validate_support(
                item["fit_support"], f"{endpoint_name}.fold{fold_index}.fit_support", require_both_classes=True
            )
            evaluation = _validate_support(
                item["evaluation_support"],
                f"{endpoint_name}.fold{fold_index}.evaluation_support",
                require_both_classes=True,
            )
            if fit["records"] > expected_records - evaluation["records"]:
                raise ValueError(f"fit support exceeds non-evaluation records for {endpoint_name}")
            if fit["patients"] > expected_patients - evaluation["patients"]:
                raise ValueError(f"fit patients exceed non-evaluation patients for {endpoint_name}")
            overlap = _nonnegative_int(item["fit_test_patient_overlap"], "fit_test_patient_overlap")
            if overlap != 0:
                raise ValueError(f"fit and outer-evaluation patients overlap for {endpoint_name}")
            prevalence = _finite_metric(item["fit_prevalence"], "fit_prevalence")
            if not 0 < prevalence < 1 or not math.isclose(
                prevalence, fit["positive_records"] / fit["records"], rel_tol=0.0, abs_tol=1e-12
            ):
                raise ValueError(f"fold prevalence does not reconcile with fit support for {endpoint_name}")
            fold_supports.append((fit, evaluation))

        evaluation_totals = {
            key: sum(item[1][key] for item in fold_supports)
            for key in SUPPORT_KEYS
        }
        if evaluation_totals != support:
            raise ValueError(f"outer-fold support does not reconcile for {endpoint_name}")

        bootstrap = _assert_exact_keys(
            endpoint["patient_cluster_bootstrap_deltas"],
            {"unit", "method", "replicates", "seed", "scope_limit", "comparisons"},
            f"{endpoint_name}.bootstrap",
        )
        if (
            bootstrap["replicates"] != expected_replicates
            or bootstrap["seed"] != expected_seed + endpoint_index
            or bootstrap["unit"] != "patient_id cluster; repeated ECGs sampled together"
            or bootstrap["method"] != "paired unstratified percentile bootstrap on pooled out-of-fold scores"
            or bootstrap["scope_limit"] != config["bootstrap"]["scope_limit"]
        ):
            raise ValueError(f"bootstrap protocol differs for {endpoint_name}")
        comparisons = _assert_exact_keys(
            bootstrap["comparisons"], set(COMPARISONS), f"{endpoint_name}.bootstrap.comparisons"
        )
        for comparison, metrics_ci in comparisons.items():
            metrics_ci = _assert_exact_keys(
                metrics_ci, set(BOOTSTRAP_METRICS), f"{endpoint_name}.{comparison}.bootstrap"
            )
            for metric, result in metrics_ci.items():
                result = _assert_exact_keys(
                    result,
                    {"valid_replicates", "invalid_replicates", "point_difference_first_minus_second", "ci95"},
                    f"{endpoint_name}.{comparison}.{metric}",
                )
                valid = _nonnegative_int(result["valid_replicates"], "valid_replicates")
                invalid = _nonnegative_int(result["invalid_replicates"], "invalid_replicates")
                if valid != expected_replicates or invalid != 0 or valid + invalid != expected_replicates:
                    raise ValueError(f"bootstrap replicate accounting fails for {endpoint_name} {metric}")
                interval = result["ci95"]
                if not isinstance(interval, list) or len(interval) != 2:
                    raise ValueError(f"bootstrap interval is missing for {endpoint_name} {metric}")
                lower, upper = (_finite_metric(item, metric) for item in interval)
                if lower > upper:
                    raise ValueError(f"bootstrap interval is reversed for {endpoint_name} {metric}")
                point = _finite_metric(result["point_difference_first_minus_second"], metric)
                if not math.isclose(
                    point, differences[comparison][metric], rel_tol=0.0, abs_tol=1e-12
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


def _load_registry_entry(path: Path, experiment_id: str) -> dict:
    registry = json.loads(path.read_text(encoding="utf-8"))
    matches = [item for item in registry.get("experiments", []) if item.get("id") == experiment_id]
    if len(matches) != 1:
        raise ValueError("registry must contain exactly one matching experiment")
    return matches[0]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--runner", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--expected-job-id", required=True)
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    config = json.loads(args.config.read_text(encoding="utf-8"))
    result = verify_aggregate(
        report,
        config,
        registry_entry=_load_registry_entry(args.registry, "B1-V46-SPH-PREVALENCE-COMPARATOR"),
        expected_job_id=args.expected_job_id,
        aggregate_sha256=sha256_file(args.report),
        config_sha256=sha256_file(args.config),
        runner_sha256=sha256_file(args.runner),
        verifier_sha256=sha256_file(Path(__file__)),
    )
    print(
        "Verified aggregate-only SPH prevalence comparison: "
        f"job {result['job_id']}, {result['records']} records, "
        f"{result['patients']} patients, {result['endpoints']} endpoints"
    )


if __name__ == "__main__":
    main()
