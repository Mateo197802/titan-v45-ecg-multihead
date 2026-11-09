"""Compare frozen-score calibration with a patient-cross-fitted prevalence baseline."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import platform
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
CALIBRATION_PATH = ROOT / "scripts/benchmarkmax/calibrate_sph_frozen_scores.py"
CALIBRATION_SPEC = importlib.util.spec_from_file_location("sph_b1_calibration", CALIBRATION_PATH)
if CALIBRATION_SPEC is None or CALIBRATION_SPEC.loader is None:
    raise RuntimeError("cannot load the frozen B1 calibration implementation")
calibration = importlib.util.module_from_spec(CALIBRATION_SPEC)
CALIBRATION_SPEC.loader.exec_module(calibration)

PROBABILITY_METRICS = ("brier", "ece", "log_loss")
BOOTSTRAP_METRICS = ("brier", "ece", "log_loss")
COMPARISONS = {
    "raw_minus_prevalence": ("raw_v45_oof", "constant_prevalence_oof"),
    "platt_minus_prevalence": ("platt_oof", "constant_prevalence_oof"),
}
FORBIDDEN_KEYS = {
    "ecg_id",
    "record_id",
    "patient_id",
    "signal",
    "waveform",
    "row_predictions",
    "per_record_scores",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _binary_labels(labels: np.ndarray) -> np.ndarray:
    values = np.asarray(labels)
    if values.ndim != 1 or values.size == 0:
        raise ValueError("labels must be a non-empty binary vector")
    if not np.isfinite(values).all() or not np.isin(values, (0, 1)).all():
        raise ValueError("labels must be binary")
    return values.astype(np.int64)


def _aligned_patients(patient_ids: np.ndarray, expected_size: int) -> np.ndarray:
    patients = np.asarray(patient_ids, dtype=str)
    if patients.shape != (expected_size,) or np.any(np.char.str_len(np.char.strip(patients)) == 0):
        raise ValueError("each row must have an aligned, non-empty patient ID")
    return np.char.strip(patients)


def cross_fitted_prevalence(
    labels: np.ndarray,
    patient_ids: np.ndarray,
    *,
    seed: int,
) -> tuple[np.ndarray, list[dict]]:
    """Estimate prevalence on each fold's calibration-fit patients only."""
    y = _binary_labels(labels)
    patients = _aligned_patients(patient_ids, y.size)
    folds = np.asarray([calibration.outer_fold(item, seed=seed) for item in patients])
    roles = np.asarray([calibration.inner_partition(item, seed=seed) for item in patients])
    scores = np.full(y.shape, np.nan, dtype=np.float64)
    fold_reports = []

    for fold in range(calibration.OUTER_FOLDS):
        test_mask = folds == fold
        fit_mask = (folds != fold) & (roles == "calibration_fit")
        fit_patient_ids = np.unique(patients[fit_mask])
        test_patient_ids = np.unique(patients[test_mask])
        overlap = int(np.intersect1d(fit_patient_ids, test_patient_ids).size)
        if overlap:
            raise AssertionError("prevalence fit and outer-evaluation patients overlap")
        if np.unique(y[fit_mask]).size != 2 or np.unique(y[test_mask]).size != 2:
            raise ValueError("prevalence fit and evaluation folds require both statement classes")
        prevalence = float(np.mean(y[fit_mask]))
        if not 0.0 < prevalence < 1.0:
            raise ValueError("fit prevalence must be strictly between zero and one")
        scores[test_mask] = prevalence
        fold_reports.append(
            {
                "fold": fold,
                "fit_support": calibration._support(y, patients, fit_mask),
                "evaluation_support": calibration._support(y, patients, test_mask),
                "fit_prevalence": prevalence,
                "fit_test_patient_overlap": overlap,
            }
        )

    if not np.isfinite(scores).all():
        raise AssertionError("every row must receive exactly one out-of-fold prevalence score")
    return scores, fold_reports


def _weights(sample_weight: np.ndarray | None, size: int) -> np.ndarray:
    if sample_weight is None:
        return np.ones(size, dtype=np.int64)
    values = np.asarray(sample_weight)
    if (
        values.shape != (size,)
        or not np.isfinite(values).all()
        or np.any(values < 0)
        or not np.equal(values, np.floor(values)).all()
    ):
        raise ValueError("sample weights must be non-negative integers aligned to rows")
    return values.astype(np.int64)


def _probability_error_metrics(
    labels: np.ndarray,
    probabilities: np.ndarray,
    weights: np.ndarray,
) -> dict[str, float]:
    y, scores = calibration._validate_binary_inputs(labels, probabilities)
    if weights.shape != y.shape or int(weights.sum()) == 0:
        raise ValueError("probability metric weights must align and have positive mass")
    total = int(weights.sum())
    residual = scores - y
    clipped = np.clip(scores, 1e-15, 1.0 - 1e-15)
    log_losses = -(y * np.log(clipped) + (1 - y) * np.log1p(-clipped))
    bins = np.minimum((scores * calibration.ECE_BINS).astype(np.int64), calibration.ECE_BINS - 1)
    count = np.bincount(bins, weights=weights, minlength=calibration.ECE_BINS)
    positive = np.bincount(bins, weights=weights * y, minlength=calibration.ECE_BINS)
    probability_sum = np.bincount(bins, weights=weights * scores, minlength=calibration.ECE_BINS)
    occupied = count > 0
    ece = np.sum(
        (count[occupied] / total)
        * np.abs(positive[occupied] / count[occupied] - probability_sum[occupied] / count[occupied])
    )
    return {
        "brier": float(np.sum(weights * residual**2) / total),
        "ece": float(ece),
        "log_loss": float(np.sum(weights * log_losses) / total),
    }


def probability_metrics(
    labels: np.ndarray,
    probabilities: np.ndarray,
    *,
    sample_weight: np.ndarray | None = None,
) -> dict[str, float | None]:
    y, scores = calibration._validate_binary_inputs(labels, probabilities)
    weights = _weights(sample_weight, y.size)
    return _probability_error_metrics(y, scores, weights)


def paired_cluster_bootstrap_deltas(
    labels: np.ndarray,
    predictions: dict[str, np.ndarray],
    patient_ids: np.ndarray,
    *,
    replicates: int,
    seed: int,
) -> dict:
    y = _binary_labels(labels)
    patients = _aligned_patients(patient_ids, y.size)
    if set(predictions) != {"raw_v45_oof", "platt_oof", "constant_prevalence_oof"}:
        raise ValueError("bootstrap requires raw, Platt, and constant-prevalence scores")
    scores = {
        name: calibration._validate_binary_inputs(y, values)[1]
        for name, values in predictions.items()
    }
    unique_patients, patient_inverse = np.unique(patients, return_inverse=True)
    if unique_patients.size < 2 or replicates < 1:
        raise ValueError("cluster bootstrap requires multiple patients and replicates")

    rng = np.random.Generator(np.random.PCG64(seed))
    deltas = {
        name: {metric: [] for metric in BOOTSTRAP_METRICS} for name in COMPARISONS
    }
    for _ in range(replicates):
        selected = rng.integers(0, unique_patients.size, size=unique_patients.size)
        patient_weights = np.bincount(selected, minlength=unique_patients.size)
        row_weights = patient_weights[patient_inverse]
        if not np.any(row_weights):
            continue
        metrics = {
            method: _probability_error_metrics(y, values, row_weights)
            for method, values in scores.items()
        }
        for comparison, (first, second) in COMPARISONS.items():
            for metric in BOOTSTRAP_METRICS:
                deltas[comparison][metric].append(metrics[first][metric] - metrics[second][metric])

    comparisons = {}
    point_metrics = {
        method: _probability_error_metrics(y, values, np.ones(y.size, dtype=np.int64))
        for method, values in scores.items()
    }
    for comparison, (first, second) in COMPARISONS.items():
        comparisons[comparison] = {}
        for metric, values in deltas[comparison].items():
            comparisons[comparison][metric] = {
                "valid_replicates": len(values),
                "invalid_replicates": replicates - len(values),
                "point_difference_first_minus_second": point_metrics[first][metric]
                - point_metrics[second][metric],
                "ci95": [float(np.quantile(values, 0.025)), float(np.quantile(values, 0.975))]
                if values
                else None,
            }
    return {
        "unit": "patient_id cluster; repeated ECGs sampled together",
        "method": "paired unstratified percentile bootstrap on pooled out-of-fold scores",
        "replicates": replicates,
        "seed": seed,
        "scope_limit": "conditional on fixed fold-specific Platt and prevalence estimates",
        "comparisons": comparisons,
    }


def _compare_metrics(actual: dict, expected: dict, label: str) -> None:
    for metric in ("records", "positive_support", "negative_support", "confusion"):
        if actual[metric] != expected[metric]:
            raise ValueError(f"recomputed B1 {label} metric differs for {metric}")
    for metric in ("auroc", "average_precision", "brier", "ece", "accuracy", "f1"):
        left, right = actual[metric], expected[metric]
        if left is None or right is None:
            if left is not right:
                raise ValueError(f"recomputed B1 {label} metric differs for {metric}")
        elif not math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=1e-12):
            raise ValueError(f"recomputed B1 {label} metric differs for {metric}")


def build_report(
    *,
    metadata_path: Path,
    ledger_path: Path,
    v45_config_path: Path,
    receipt_path: Path,
    baseline_path: Path,
    b1_config_path: Path,
    b1_result_path: Path,
    protocol_path: Path,
    config_path: Path,
    script_path: Path,
    commit: str,
    slurm_job_id: str,
    runtime: dict[str, str],
) -> dict:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    expected_inputs = config["input_sha256"]
    b1_config_sha = sha256_file(b1_config_path)
    b1_result_sha = sha256_file(b1_result_path)
    protocol_sha = sha256_file(protocol_path)
    script_sha = sha256_file(script_path)
    if b1_config_sha != config["source_b1_config_sha256"]:
        raise ValueError("source B1 configuration hash differs from the frozen comparator config")
    if b1_result_sha != config["source_b1_result_sha256"]:
        raise ValueError("source B1 result hash differs from the frozen comparator config")
    if protocol_sha != config["protocol_sha256"]:
        raise ValueError("prevalence protocol hash differs from the frozen comparator config")
    if runtime != config["runtime"]["versions"]:
        raise ValueError("runtime differs from the frozen prevalence comparator configuration")

    b1_config, receipt, _, _, actual_inputs = calibration._validate_inputs(
        metadata_path,
        ledger_path,
        v45_config_path,
        receipt_path,
        baseline_path,
        b1_config_path,
    )
    if actual_inputs != expected_inputs:
        raise ValueError("frozen input hashes differ from the prevalence comparator configuration")
    if (
        int(b1_config["seed"]) != int(config["source"]["b1_protocol_seed"])
        or calibration.OUTER_FOLDS != int(config["source"]["b1_outer_folds"])
        or int(b1_config["source"]["records"]) != int(config["source"]["records"])
        or int(b1_config["source"]["patients"]) != int(config["source"]["patients"])
    ):
        raise ValueError("source B1 split or population differs from the frozen comparator config")
    b1_report = json.loads(b1_result_path.read_text(encoding="utf-8"))
    if b1_report.get("execution", {}).get("script_sha256") != config["source_b1_runner_sha256"]:
        raise ValueError("source B1 result does not identify the frozen calibration runner")
    if b1_report.get("input_sha256") != actual_inputs:
        raise ValueError("source B1 result input hashes differ from the verified inputs")

    metadata, patients_by_record = calibration._load_metadata(metadata_path)
    ledger = calibration._load_ledger(ledger_path, b1_config["endpoints"])
    if metadata.keys() != ledger.keys():
        raise ValueError("metadata and ledger record sets differ")
    if len(metadata) != int(config["source"]["records"]):
        raise ValueError("source record count differs from the frozen comparator configuration")
    if len(set(patients_by_record.values())) != int(config["source"]["patients"]):
        raise ValueError("source patient count differs from the frozen comparator configuration")

    endpoints = {}
    for index, target in enumerate(b1_config["endpoints"]):
        profile, name, code = target["profile"], target["name"], int(target["code"])
        key = f"{profile}:{name}"
        record_ids = list(metadata)
        labels = np.asarray([int(code in metadata[record]["codes"]) for record in record_ids])
        patients = np.asarray([patients_by_record[record] for record in record_ids], dtype=str)
        scores = np.asarray(
            [float(ledger[record][profile]["scores"][name]) for record in record_ids],
            dtype=np.float64,
        )
        nested = calibration.nested_patient_calibration(
            labels, scores, patients, seed=int(b1_config["seed"])
        )
        raw_metrics = calibration.binary_metrics(
            labels, scores, decisions=nested["raw_threshold_decisions"]
        )
        platt_scores = nested["calibrated_probabilities"]
        platt_metrics = calibration.binary_metrics(
            labels,
            platt_scores,
            decisions=nested["calibrated_threshold_decisions"],
        )
        original = b1_report["endpoints"][key]
        source_support = {
            "records": int(labels.size),
            "patients": int(np.unique(patients).size),
            "positive_records": int(labels.sum()),
            "negative_records": int(labels.size - labels.sum()),
            "positive_patients": int(np.unique(patients[labels == 1]).size),
        }
        original_support = original["source_support"]
        if source_support != {
            "records": original_support["records"],
            "patients": original_support["patients"],
            "positive_records": original_support["positive_records"],
            "negative_records": original_support["negative_records"],
            "positive_patients": original_support["patients_with_positive_records"],
        }:
            raise ValueError(f"source endpoint support differs from the frozen B1 aggregate for {key}")
        _compare_metrics(raw_metrics, original["raw_nested_cv"]["metrics"], "raw")
        _compare_metrics(platt_metrics, original["platt_nested_cv"]["metrics"], "Platt")

        prevalence_scores, prevalence_folds = cross_fitted_prevalence(
            labels, patients, seed=int(b1_config["seed"])
        )
        score_sets = {
            "raw_v45_oof": scores,
            "platt_oof": platt_scores,
            "constant_prevalence_oof": prevalence_scores,
        }
        method_metrics = {
            method: probability_metrics(labels, values)
            for method, values in score_sets.items()
        }
        point_differences = {
            comparison: {
                metric: method_metrics[first][metric] - method_metrics[second][metric]
                for metric in PROBABILITY_METRICS
                if method_metrics[first][metric] is not None
                and method_metrics[second][metric] is not None
            }
            for comparison, (first, second) in COMPARISONS.items()
        }
        bootstrap_config = config["bootstrap"]
        bootstrap = paired_cluster_bootstrap_deltas(
            labels,
            score_sets,
            patients,
            replicates=int(bootstrap_config["replicates"]),
            seed=int(bootstrap_config["base_seed"]) + index,
        )
        for comparison, metrics in bootstrap["comparisons"].items():
            for metric, item in metrics.items():
                item["point_difference_first_minus_second"] = point_differences[comparison][metric]

        endpoints[key] = {
            "reference": target["reference"],
            "source_support": source_support,
            "metrics": method_metrics,
            "point_differences": point_differences,
            "patient_cluster_bootstrap_deltas": bootstrap,
            "fold_support": prevalence_folds,
        }

    return {
        "schema": "TITAN_V46_SPH_B1_PREVALENCE_COMPARISON_V1",
        "scope": (
            "Supplementary exploratory analysis of previously observed SPH predictions; "
            "not an independent, locked, confirmatory, or clinical validation."
        ),
        "source": {
            "records": len(metadata),
            "patients": len(set(patients_by_record.values())),
            "reference": "presence of the frozen primary ECG statement code; absence is not adjudicated disease absence",
        },
        "design": {
            "outer_folds": calibration.OUTER_FOLDS,
            "seed": int(b1_config["seed"]),
            "patient_assignment_uses_labels": False,
            "fit_evaluation_patient_overlap": 0,
            "prevalence_estimator": config["prevalence_estimator"],
            "fit_partition_matches_platt": True,
            "constant_baseline_has_no_fitted_threshold": True,
            "metrics": list(PROBABILITY_METRICS),
            "bootstrap_metrics": list(BOOTSTRAP_METRICS),
            "all_sph_previously_observed": True,
            "confirmatory_external_test": False,
        },
        "input_sha256": actual_inputs,
        "source_b1_config_sha256": b1_config_sha,
        "source_b1_result_sha256": b1_result_sha,
        "source_b1_runner_sha256": config["source_b1_runner_sha256"],
        "protocol_sha256": protocol_sha,
        "individual_identifiers_exported": False,
        "record_level_scores_exported": False,
        "raw_signals_exported": False,
        "endpoints": endpoints,
        "execution": {
            "commit": commit,
            "slurm_job_id": slurm_job_id,
            "script_sha256": script_sha,
            "config_sha256": sha256_file(config_path),
            "runtime": {
                "environment": config["runtime"]["environment"],
                "versions": runtime,
            },
        },
    }


def _assert_outside(path: Path, roots: list[Path], label: str) -> None:
    resolved = path.resolve()
    for root in roots:
        try:
            resolved.relative_to(root.resolve())
        except ValueError:
            continue
        raise ValueError(f"{label} must remain outside all Git checkouts")


def _runtime_versions() -> dict[str, str]:
    import scipy

    return {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
    }


def run(args: argparse.Namespace) -> None:
    output = args.output.resolve()
    roots = [ROOT, *(path.resolve() for path in args.forbidden_root)]
    _assert_outside(output, roots, "private prevalence comparison aggregate")
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()
    if status:
        raise ValueError("BenchmarkMax checkout must be clean for frozen prevalence execution")
    config = json.loads(args.config.read_text(encoding="utf-8"))
    runtime = _runtime_versions()
    if runtime != config["runtime"]["versions"]:
        raise ValueError("runtime differs from the frozen prevalence comparator configuration")
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()
    report = build_report(
        metadata_path=args.metadata,
        ledger_path=args.ledger,
        v45_config_path=args.v45_config,
        receipt_path=args.scoring_receipt,
        baseline_path=args.baseline_aggregate,
        b1_config_path=args.b1_config,
        b1_result_path=args.b1_result,
        protocol_path=args.protocol,
        config_path=args.config,
        script_path=Path(__file__),
        commit=commit,
        slurm_job_id=os.environ.get("SLURM_JOB_ID", "not_slurm"),
        runtime=runtime,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    os.chmod(output, 0o600)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--v45-config", type=Path, required=True)
    parser.add_argument("--scoring-receipt", type=Path, required=True)
    parser.add_argument("--baseline-aggregate", type=Path, required=True)
    parser.add_argument("--b1-config", type=Path, required=True)
    parser.add_argument("--b1-result", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--forbidden-root", type=Path, action="append", default=[])
    run(parser.parse_args())


if __name__ == "__main__":
    main()
