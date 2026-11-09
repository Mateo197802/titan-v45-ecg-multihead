from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import math
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/benchmarkmax/calibrate_sph_frozen_scores.py"
spec = importlib.util.spec_from_file_location("sph_calibration", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_patient_folds_are_stable_and_keep_each_patient_in_one_fold():
    patients = [f"patient-{index}" for index in range(500)]
    assignments = {patient: module.outer_fold(patient) for patient in patients}
    assert assignments == {
        patient: module.outer_fold(patient) for patient in reversed(patients)
    }
    assert set(assignments.values()) == set(range(module.OUTER_FOLDS))
    assert module.outer_fold("repeated-patient") == module.outer_fold("repeated-patient")


def test_platt_scaling_is_finite_monotone_and_corrects_miscalibration():
    rng = np.random.default_rng(197802)
    raw = np.linspace(0.01, 0.99, 1000)
    logits = np.log(raw / (1.0 - raw))
    true_probability = 1.0 / (1.0 + np.exp(-(-0.8 + 0.72 * logits)))
    labels = rng.binomial(1, true_probability)

    intercept, slope = module.fit_platt(labels, raw)
    calibrated = module.apply_platt(raw, intercept, slope)

    assert math.isfinite(intercept)
    assert 0 < slope <= module.MAX_PLATT_SLOPE
    assert np.isfinite(calibrated).all()
    assert np.all(np.diff(calibrated) > 0)
    assert np.mean((calibrated - labels) ** 2) < np.mean((raw - labels) ** 2)


def test_f1_threshold_uses_deterministic_conservative_tie_break():
    labels = np.array([1, 0, 1, 0], dtype=np.int64)
    probabilities = np.array([0.8, 0.7, 0.6, 0.1], dtype=np.float64)
    threshold = module.select_f1_threshold(labels, probabilities)
    assert threshold == 0.6


def test_binary_metrics_support_patient_cluster_weights():
    labels = np.array([1, 1, 0, 0], dtype=np.int64)
    probabilities = np.array([0.8, 0.2, 0.1, 0.7], dtype=np.float64)
    repeated = np.array([0, 0, 2, 3])

    weighted = module.binary_metrics(
        labels,
        probabilities,
        threshold=0.5,
        sample_weight=np.array([2, 0, 1, 1], dtype=np.int64),
    )
    expanded = module.binary_metrics(
        labels[repeated], probabilities[repeated], threshold=0.5
    )

    assert weighted["confusion"] == expanded["confusion"]
    for metric in ("sensitivity", "specificity", "ppv", "f1", "auroc", "average_precision", "brier", "ece"):
        assert math.isclose(weighted[metric], expanded[metric], rel_tol=1e-12, abs_tol=1e-12)
    with pytest.raises(ValueError, match="binary"):
        module.binary_metrics(np.array([0.5, 1.0]), np.array([0.1, 0.9]), threshold=0.5)
    with pytest.raises(ValueError, match="weights"):
        module.binary_metrics(
            np.array([0, 1]),
            np.array([0.1, 0.9]),
            threshold=0.5,
            sample_weight=np.array([1.5, 1.0]),
        )


def test_cluster_bootstrap_covers_all_reported_performance_metrics():
    labels = np.array([1, 0, 1, 0, 1, 0], dtype=np.int64)
    scores = np.array([0.8, 0.2, 0.4, 0.6, 0.7, 0.3], dtype=np.float64)
    decisions = scores >= 0.5
    patients = np.array(["p1", "p1", "p2", "p3", "p4", "p5"])

    result = module.paired_cluster_bootstrap_delta(
        labels,
        scores,
        scores,
        decisions,
        decisions,
        patients,
        replicates=20,
        seed=17,
    )

    assert set(result["intervals"]) == {
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
    }


def test_cluster_bootstrap_rejects_empty_patient_ids():
    labels = np.array([1, 0, 1, 0], dtype=np.int64)
    scores = np.array([0.8, 0.2, 0.4, 0.6], dtype=np.float64)
    decisions = scores >= 0.5
    with pytest.raises(ValueError, match="patient IDs"):
        module.paired_cluster_bootstrap_delta(
            labels,
            scores,
            scores,
            decisions,
            decisions,
            np.array(["p1", "", "p2", "p3"]),
            replicates=20,
            seed=17,
        )


def test_build_report_reconciles_baseline_and_exports_only_aggregates(tmp_path):
    patient_count = 500
    count = patient_count * 2
    metadata_path = tmp_path / "metadata.csv"
    ledger_path = tmp_path / "private-predictions.jsonl"
    v45_config_path = tmp_path / "v45-config.json"
    receipt_path = tmp_path / "scoring-receipt.json"
    baseline_path = tmp_path / "baseline-aggregate.json"
    b1_config_path = tmp_path / "b1-config.json"
    target = {
        "profile": "P4",
        "name": "ASMI",
        "code": 165,
        "v45_frozen_threshold": 0.5,
        "reference": "synthetic test endpoint",
    }
    model_hashes = {"synthetic-model": "a" * 64}
    with metadata_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["ECG_ID", "Patient_ID", "AHA_Code"])
        writer.writeheader()
        for index in range(count):
            patient_index = index // 2
            writer.writerow(
                {
                    "ECG_ID": f"private-ecg-{index}",
                    "Patient_ID": f"private-patient-{patient_index}",
                    "AHA_Code": "165" if patient_index % 3 == 0 else "",
                }
            )

    labels = np.asarray(
        [int((index // 2) % 3 == 0) for index in range(count)], dtype=np.int64
    )
    scores = np.asarray(
        [
            (0.35 if index % 10 == 0 else 0.75)
            if labels[index]
            else (0.65 if index % 10 == 0 else 0.25)
            for index in range(count)
        ],
        dtype=np.float64,
    )
    decisions = scores >= target["v45_frozen_threshold"]
    ledger_rows = []
    for index, (score, decision) in enumerate(zip(scores, decisions, strict=True)):
        ledger_rows.append(
            {
                "record_id": f"private-ecg-{index}",
                "status": "scored",
                "profiles": {
                    "P4": {
                        "scores": {"ASMI": float(score)},
                        "labels": ["ASMI"] if decision else [],
                        "used_fallback": False,
                    }
                },
            }
        )
    ledger_path.write_text(
        "".join(json.dumps(row, separators=(",", ":")) + "\n" for row in ledger_rows),
        encoding="utf-8",
    )

    v45_config = {
        "expected_source_records": count,
        "thresholds": {"P4": {"ASMI": target["v45_frozen_threshold"]}},
        "endpoints": [{"profile": "P4", "name": "ASMI", "codes": [165]}],
        "model_sha256": model_hashes,
    }
    v45_config_path.write_text(json.dumps(v45_config), encoding="utf-8")
    hashes = {
        "metadata": hashlib.sha256(metadata_path.read_bytes()).hexdigest(),
        "ledger": hashlib.sha256(ledger_path.read_bytes()).hexdigest(),
        "v45_frozen_config": hashlib.sha256(v45_config_path.read_bytes()).hexdigest(),
    }
    receipt = {
        "ledger_sha256": hashes["ledger"],
        "source_sha256": {"metadata.csv": hashes["metadata"]},
        "protocol_commit": "synthetic-protocol-commit",
        "protocol_sha256": "b" * 64,
        "model_sha256": model_hashes,
    }
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    hashes["scoring_receipt"] = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
    frozen = module.binary_metrics(labels, scores, decisions=decisions)
    baseline = {
        "scoring_ledger_sha256": hashes["ledger"],
        "scoring_receipt_sha256": hashes["scoring_receipt"],
        "endpoints": {
            "P4:ASMI": {
                "metrics": {**frozen["confusion"], "rows": count}
            }
        },
    }
    baseline_path.write_text(json.dumps(baseline), encoding="utf-8")
    hashes["baseline_aggregate"] = hashlib.sha256(baseline_path.read_bytes()).hexdigest()
    config = {
        "source": {
            "records": count,
            "v45_protocol_commit": receipt["protocol_commit"],
            "v45_protocol_config_sha256": receipt["protocol_sha256"],
            "patients": patient_count,
        },
        "input_sha256": hashes,
        "expected_records": count,
        "seed": 197802,
        "bootstrap": {
            "replicates": 5,
            "base_seed": 197813,
            "delta_metrics": list(module.BOOTSTRAP_METRICS),
        },
        "endpoints": [target],
    }
    b1_config_path.write_text(json.dumps(config), encoding="utf-8")

    report = module.build_report(
        metadata_path,
        ledger_path,
        v45_config_path,
        receipt_path,
        baseline_path,
        b1_config_path,
        script_path=SCRIPT,
        slurm_job_id="test-job",
        commit="test-commit",
    )

    serialized = json.dumps(report)
    assert report["individual_identifiers_exported"] is False
    assert report["record_level_outputs_exported"] is False
    assert "private-ecg-0" not in serialized
    assert "private-patient-0" not in serialized
    assert report["endpoints"]["P4:ASMI"]["v45_frozen_baseline"]["metrics"]["confusion"] == frozen["confusion"]
    assert len(report["endpoints"]["P4:ASMI"]["fold_support"]) == module.OUTER_FOLDS

    config["bootstrap"]["delta_metrics"] = ["f1"]
    b1_config_path.write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(ValueError, match="bootstrap metric list"):
        module.build_report(
            metadata_path,
            ledger_path,
            v45_config_path,
            receipt_path,
            baseline_path,
            b1_config_path,
            script_path=SCRIPT,
            slurm_job_id="test-job",
            commit="test-commit",
        )

    config["bootstrap"]["delta_metrics"] = list(module.BOOTSTRAP_METRICS)
    config["source"]["records"] = count + 1
    b1_config_path.write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(ValueError, match="source population"):
        module.build_report(
            metadata_path,
            ledger_path,
            v45_config_path,
            receipt_path,
            baseline_path,
            b1_config_path,
            script_path=SCRIPT,
            slurm_job_id="test-job",
            commit="test-commit",
        )
