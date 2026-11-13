from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERIFIER = ROOT / "scripts/benchmarkmax/verify_sph_b1_aggregate.py"
RENDERER = ROOT / "scripts/benchmarkmax/render_sph_b1_figure.py"
CALIBRATOR = ROOT / "scripts/benchmarkmax/calibrate_sph_frozen_scores.py"
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


def _metric_block() -> dict:
    return {
        "records": 4,
        "positive_support": 2,
        "negative_support": 2,
        "predicted_positive_support": 2,
        "confusion": {"tp": 1, "fp": 1, "tn": 1, "fn": 1},
        "accuracy": 0.5,
        "sensitivity": 0.5,
        "specificity": 0.5,
        "ppv": 0.5,
        "npv": 0.5,
        "f1": 0.5,
        "auroc": 0.5,
        "average_precision": 0.5,
        "brier": 0.25,
        "ece": 0.1,
    }


def _fixture(tmp_path: Path) -> tuple[Path, Path]:
    config_path = tmp_path / "config.json"
    report_path = tmp_path / "report.json"
    input_hashes = {name: str(index) * 64 for index, name in enumerate(
        ("metadata", "ledger", "v45_frozen_config", "scoring_receipt", "baseline_aggregate"),
        start=1,
    )}
    bootstrap = {"replicates": 2, "delta_metrics": list(METRICS)}
    config = {
        "schema": "TITAN_V46_SPH_B1_CALIBRATION_PROTOCOL_V1",
        "source": {
            "records": 4,
            "patients": 3,
            "v45_protocol_commit": "v45-protocol",
        },
        "input_sha256": input_hashes,
        "expected_records": 4,
        "runtime": {
            "environment": "synthetic test runtime",
            "versions": {"python": "3.10.18", "numpy": "1.26.4", "scipy": "1.15.3"},
        },
        "metrics": {"bootstrap": bootstrap},
        "endpoints": [{"profile": "P4", "name": "ASMI"}],
    }
    config_path.write_text(json.dumps(config), encoding="utf-8")

    intervals = {
        name: {
            "valid_replicates": 2,
            "invalid_replicates": 0,
            "bootstrap_mean_difference_calibrated_minus_raw": 0.0,
            "ci95": [-0.1, 0.1],
            "point_difference_calibrated_minus_raw": 0.0,
        }
        for name in METRICS
    }
    endpoint = {
        "source_support": {
            "records": 4,
            "patients": 3,
            "positive_records": 2,
            "negative_records": 2,
            "patients_with_positive_records": 2,
        },
        "v45_frozen_baseline": {"metrics": _metric_block()},
        "raw_nested_cv": {"metrics": _metric_block()},
        "platt_nested_cv": {"metrics": _metric_block()},
        "platt_at_0_5_reference_operating_point": {"metrics": _metric_block()},
        "paired_patient_cluster_bootstrap_delta": {"replicates": 2, "intervals": intervals},
        "fold_support": [
            {
                "fit": {
                    "records": 2,
                    "patients": 1,
                    "positive_records": 1,
                    "positive_patients": 1,
                    "negative_records": 1,
                },
                "threshold_tune": {
                    "records": 1,
                    "patients": 1,
                    "positive_records": 1,
                    "positive_patients": 1,
                    "negative_records": 0,
                },
                "test": {
                    "records": 1,
                    "patients": 1,
                    "positive_records": 0,
                    "positive_patients": 0,
                    "negative_records": 1,
                },
            }
            for _ in range(5)
        ],
    }
    report = {
        "schema": "TITAN_V46_SPH_B1_CALIBRATION_DIAGNOSTIC_V1",
        "scope": "Exploratory V4.6 adaptation diagnostic; not independent or confirmatory.",
        "source": {"records": 4, "patients": 3, "reference": "synthetic ECG statement"},
        "design": {
            "all_spH_already_observed": True,
            "confirmatory_external_test": False,
            "fit_tune_test_patient_overlap": 0,
        },
        "input_sha256": input_hashes,
        "source_v45_protocol_commit": "v45-protocol",
        "source_v45_model_sha256": {"model": "a" * 64},
        "individual_identifiers_exported": False,
        "record_level_outputs_exported": False,
        "endpoints": {"P4:ASMI": endpoint},
        "execution": {
            "commit": "b" * 40,
            "slurm_job_id": "32758",
            "script_sha256": hashlib.sha256(CALIBRATOR.read_bytes()).hexdigest(),
            "b1_config_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
            "runtime": config["runtime"],
        },
    }
    report_path.write_text(json.dumps(report), encoding="utf-8")
    return report_path, config_path


def _run_verifier(report: Path, config: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable,
            str(VERIFIER),
            "--report",
            str(report),
            "--config",
            str(config),
            "--calibrator",
            str(CALIBRATOR),
            "--expected-job-id",
            "32758",
        ],
        check=False,
        capture_output=True,
        text=True,
    )


def test_verifier_accepts_sanitized_aggregate_and_checks_provenance(tmp_path):
    report_path, config_path = _fixture(tmp_path)

    result = _run_verifier(report_path, config_path)

    assert result.returncode == 0, result.stderr
    assert "verified" in result.stdout.lower()


def test_verifier_rejects_confusion_denominator_mismatch(tmp_path):
    report_path, config_path = _fixture(tmp_path)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["endpoints"]["P4:ASMI"]["raw_nested_cv"]["metrics"]["confusion"]["tp"] = 2
    report_path.write_text(json.dumps(report), encoding="utf-8")

    result = _run_verifier(report_path, config_path)

    assert result.returncode != 0
    assert "confusion" in result.stderr.lower()


def test_verifier_rejects_confusion_metrics_that_do_not_reconcile(tmp_path):
    report_path, config_path = _fixture(tmp_path)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    metrics = report["endpoints"]["P4:ASMI"]["raw_nested_cv"]["metrics"]
    metrics["confusion"] = {"tp": 2, "fp": 0, "tn": 2, "fn": 0}
    report_path.write_text(json.dumps(report), encoding="utf-8")

    result = _run_verifier(report_path, config_path)

    assert result.returncode != 0
    assert "reconcile" in result.stderr.lower()


def test_verifier_rejects_positive_patients_above_partition_support(tmp_path):
    report_path, config_path = _fixture(tmp_path)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["endpoints"]["P4:ASMI"]["fold_support"][0]["fit"]["positive_patients"] = 2
    report_path.write_text(json.dumps(report), encoding="utf-8")

    result = _run_verifier(report_path, config_path)

    assert result.returncode != 0
    assert "positive patients" in result.stderr.lower()


def test_verifier_rejects_bootstrap_delta_inconsistent_with_point_metrics(tmp_path):
    report_path, config_path = _fixture(tmp_path)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["endpoints"]["P4:ASMI"]["paired_patient_cluster_bootstrap_delta"]["intervals"]["brier"][
        "point_difference_calibrated_minus_raw"
    ] = 0.1
    report_path.write_text(json.dumps(report), encoding="utf-8")

    result = _run_verifier(report_path, config_path)

    assert result.returncode != 0
    assert "point difference" in result.stderr.lower()


def test_verifier_rejects_patient_level_fields(tmp_path):
    report_path, config_path = _fixture(tmp_path)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["patient_id"] = "synthetic-private-id"
    report_path.write_text(json.dumps(report), encoding="utf-8")

    result = _run_verifier(report_path, config_path)

    assert result.returncode != 0
    assert "patient-level" in result.stderr.lower()


def test_renderer_creates_static_paired_delta_figure(tmp_path):
    report_path, _ = _fixture(tmp_path)
    output_path = tmp_path / "b1-deltas.png"

    result = subprocess.run(
        [sys.executable, str(RENDERER), "--report", str(report_path), "--output", str(output_path)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert output_path.is_file()
    assert output_path.stat().st_size > 5_000
