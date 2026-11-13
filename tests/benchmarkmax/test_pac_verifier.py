from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "verify_sph_pac_head_aggregate",
    ROOT / "scripts/benchmarkmax/verify_sph_pac_head_aggregate.py",
)
assert SPEC is not None and SPEC.loader is not None
VERIFIER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFIER)


def test_independent_verifier_checks_protocol_and_runtime_hashes(tmp_path: Path) -> None:
    inputs = {
        name: "a" * 64
        for name in (
            "metadata", "dictionary", "waveform_archive", "source_inventory", "backbone",
            "p8_specialist", "v45_p8_score_ledger", "v45_p8_scoring_receipt",
        )
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
    config = {
        "input_sha256": inputs,
        "p8_baseline": {
            "job_id": "32668",
            "ledger_sha256": inputs["v45_p8_score_ledger"],
            "receipt_sha256": inputs["v45_p8_scoring_receipt"],
            "checkpoint_sha256": inputs["p8_specialist"],
            "threshold": 0.45,
        },
        "runtime": {
            "python": "3.11.14", "numpy": "2.2.6", "scipy": "1.15.3",
            "torch": "2.10.0+cu128", "cuda": "12.8", "h5py": "3.13.0",
            "device": "NVIDIA A100-SXM4-40GB",
        },
        "runtime_archives_sha256": {
            "python_dependencies": "d" * 64,
            "h5py_dependencies": "e" * 64,
        },
        "metrics": {
            "confidence_intervals": {
                "replicates": 10,
                "seed": 197813,
                "method": "paired unstratified percentile bootstrap",
            }
        },
    }
    config_path = tmp_path / "config.json"
    protocol_path = tmp_path / "protocol.md"
    report_path = tmp_path / "aggregate.json"
    artifact_path = tmp_path / "heads.pt"
    artifact_path.write_bytes(b"private synthetic model artifact")
    config_path.write_text(json.dumps(config), encoding="utf-8")
    protocol_path.write_text("Frozen synthetic verifier fixture\n", encoding="utf-8")
    mlp_seeds = (197802, 197803, 197804, 197805, 197806)
    model_names = (
        "frozen_v45_p8_pac", "logistic_regression",
        *(f"mlp_seed_{seed}" for seed in mlp_seeds),
    )
    models = {}
    for name in model_names:
        threshold = 0.45 if name == "frozen_v45_p8_pac" else 0.5
        model_metrics = {**metrics, "threshold": threshold}
        model = {
            "threshold": threshold,
            "development_average_precision": 1.0,
            "exploratory_holdout_metrics": model_metrics,
        }
        if name.startswith("mlp_seed_"):
            model["seed"] = int(name.removeprefix("mlp_seed_"))
        models[name] = model

    pairs = {"logistic_regression_minus_frozen_v45_p8_pac": (
        "frozen_v45_p8_pac", "logistic_regression",
    )}
    for seed in mlp_seeds:
        name = f"mlp_seed_{seed}"
        pairs[f"{name}_minus_frozen_v45_p8_pac"] = ("frozen_v45_p8_pac", name)
        pairs[f"{name}_minus_logistic_regression"] = ("logistic_regression", name)

    report = {
        "schema": "TITAN_V46_SPH_PAC_HEAD_COMPARISON_V2",
        "scope": "exploratory only",
        "protocol": {
            "config_sha256": VERIFIER.sha256_file(config_path),
            "protocol_sha256": VERIFIER.sha256_file(protocol_path),
            "runner_sha256": VERIFIER.sha256_file(
                ROOT / "scripts/benchmarkmax/run_sph_pac_head_comparison.py"
            ),
            "verifier_sha256": VERIFIER.sha256_file(
                ROOT / "scripts/benchmarkmax/verify_sph_pac_head_aggregate.py"
            ),
            "slurm_wrapper_sha256": VERIFIER.sha256_file(
                ROOT / "scripts/cedia/run_sph_pac_head_comparison.sbatch"
            ),
            "git_commit": "b" * 40,
        },
        "inputs": inputs,
        "p8_baseline": {
            "job_id": "32668",
            "ledger_sha256": inputs["v45_p8_score_ledger"],
            "receipt_sha256": inputs["v45_p8_scoring_receipt"],
            "checkpoint_sha256": inputs["p8_specialist"],
            "threshold": 0.45,
        },
        "runtime_archives_sha256": config["runtime_archives_sha256"],
        "cohort": {
            "source_records": 6,
            "source_patients": 6,
            "eligible_records": 6,
            "baseline_p8_scores_available_source_records": 6,
            "baseline_p8_common_eligible_records": 6,
            "patient_overlap_across_splits": 0,
            "labels_used_for_split_assignment": False,
            "split_support": {
                "train": {"records": 2, "patients": 2, "positive_records": 1, "positive_patients": 1},
                "development": {"records": 2, "patients": 2, "positive_records": 1, "positive_patients": 1},
                "exploratory_holdout": {"records": 2, "patients": 2, "positive_records": 1, "positive_patients": 1},
            },
        },
        "models": models,
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
        "private_model_artifact": {
            "filename": artifact_path.name,
            "sha256": VERIFIER.sha256_file(artifact_path),
        },
        "runtime": {key: config["runtime"][key] for key in (
            "python", "numpy", "scipy", "torch", "cuda", "h5py",
        )},
        "execution": {"device_name": "NVIDIA A100-SXM4-40GB"},
        "privacy": {
            "individual_identifiers_exported": False,
            "record_level_scores_exported": False,
            "raw_signals_exported": False,
            "embeddings_exported": False,
        },
    }
    report_path.write_text(json.dumps(report), encoding="utf-8")

    result = VERIFIER.verify_report(report_path, config_path, protocol_path, artifact_path)

    assert result["status"] == "aggregate_schema_hash_denominator_and_privacy_checks_passed"
    assert result["holdout_records"] == 2
    artifact_path.write_bytes(b"tampered private artifact")
    with pytest.raises(ValueError, match="private model artifact hash"):
        VERIFIER.verify_report(report_path, config_path, protocol_path, artifact_path)
