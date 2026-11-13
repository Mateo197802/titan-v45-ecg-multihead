from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "verify_sph_postdedup_feasibility",
    ROOT / "scripts/benchmarkmax/verify_sph_postdedup_feasibility.py",
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def _split_support(records: dict[str, int], patients: dict[str, int], positives: dict[str, int]):
    endpoints = {}
    for endpoint in ("ASMI", "IMI", "LVH", "PAC", "PVC", "RBBB"):
        endpoints[endpoint] = {
            "positive_records": positives[endpoint],
            "statement_not_recorded_records": records["records"] - positives[endpoint],
            "positive_patients": min(positives[endpoint], patients["patients"]),
        }
    return {
        "records": records["records"],
        "patients": patients["patients"],
        "endpoints": endpoints,
    }


def _report_and_config():
    config = json.loads(
        (ROOT / "configs/benchmarkmax/sph_postdedup_support.json").read_text(encoding="utf-8")
    )
    expected = config["expected_signal_audit"]
    names = ("train", "development", "exploratory_holdout")
    before_records = dict(zip(names, (18039, 3865, 3866), strict=True))
    before_patients = dict(zip(names, (18000, 3600, 3066), strict=True))
    after_records = dict(zip(names, (17800, 3800, 3834), strict=True))
    after_patients = dict(zip(names, (17600, 3500, 3000), strict=True))
    before = {}
    after = {}
    counts = config["source"]["source_statement_counts_before_signal_exclusions"]
    for index, name in enumerate(names):
        pre_positive = {
            endpoint: count // 3 + (index < count % 3)
            for endpoint, count in counts.items()
        }
        post_positive = {endpoint: min(value, after_records[name]) for endpoint, value in pre_positive.items()}
        before[name] = _split_support(
            {"records": before_records[name]}, {"patients": before_patients[name]}, pre_positive
        )
        after[name] = _split_support(
            {"records": after_records[name]}, {"patients": after_patients[name]}, post_positive
        )
    report = {
        "schema": "TITAN_V46_SPH_POSTDEDUP_SUPPORT_V1",
        "status": "completed_aggregate_support_audit",
        "scope": (
            "Exploratory SPH development-support counts only. SPH has been previously observed; "
            "this is not performance evaluation, independent validation, or model-specific input validation."
        ),
        "source": {
            "name": "SPH ECG dataset V1",
            "records": expected["records"],
            "patients": expected["patients"],
            "input_sha256": config["source"]["input_sha256"],
            "source_inventory_reference_sha256": config["source"]["source_inventory_reference_sha256"],
        },
        "runtime": config["runtime"],
        "signal_audit": {
            "eligibility": "10-60 seconds at 500 Hz; readable finite 12-lead HDF5; at least one non-flat lead",
            "fingerprint": "SHA-256 of canonical little-endian float64 raw signal array bytes",
            "duplicate_policy": "exclude every record participating in an exact-signal duplicate group before label join",
            "near_duplicate_detection": False,
            "counts": {
                "archive_members_seen": expected["records"],
                "source_records": expected["records"],
                "valid_signal_records": expected["valid_signal_records"],
                "exact_duplicate_signal_groups": expected["exact_duplicate_signal_groups"],
                "exact_duplicate_signal_excess_records": expected["exact_duplicate_signal_excess_records"],
                "exact_duplicate_records_excluded": expected["exact_duplicate_records_excluded"],
                "unique_signal_records": expected["unique_signal_records"],
            },
        },
        "split": {
            "namespace": "TITAN-V46-SPH-DEV-SPLIT-V1:",
            "seed": "197802",
            "algorithm": "SHA-256(namespace + seed + patient ID); first 64 digest bits interpreted big-endian modulo 100",
            "assignment": {"train": "0-69", "development": "70-84", "exploratory_holdout": "85-99"},
            "labels_used_for_assignment": False,
            "patient_overlap_across_splits": 0,
            "third_partition_caveat": "This bucket was used as the exploratory holdout in the PAC pilot; it is not an untouched or confirmatory test.",
        },
        "reference": "AHA code present on this ECG. Absence means statement not recorded, not adjudicated clinical absence.",
        "endpoints": config["endpoints"],
        "support_before_signal_exclusions": {
            "record_denominator": expected["records"],
            "individual_identifiers_exported": False,
            "splits": before,
        },
        "support_after_signal_and_duplicate_exclusions": {
            "record_denominator": expected["unique_signal_records"],
            "individual_identifiers_exported": False,
            "splits": after,
        },
        "model_specific_preprocessing_assessed": False,
        "performance_metrics_computed": False,
        "individual_identifiers_exported": False,
        "execution": {"commit": "a" * 40, "slurm_job_id": "123", "script_sha256": "b" * 64, "config_sha256": "c" * 64},
    }
    return report, config


def test_verifier_accepts_consistent_aggregate_only_report():
    report, config = _report_and_config()
    receipt = module.verify_report(report, config)
    assert receipt["status"] == "passed"
    assert receipt["individual_identifiers_exported"] is False


def test_verifier_rejects_bad_denominator_or_patient_leakage():
    report, config = _report_and_config()
    report["support_after_signal_and_duplicate_exclusions"]["splits"]["train"]["records"] += 1
    with pytest.raises(ValueError, match="denominator"):
        module.verify_report(report, config)

    report, config = _report_and_config()
    report["individual_identifiers_exported"] = True
    with pytest.raises(ValueError, match="identifiers"):
        module.verify_report(report, config)

    report, config = _report_and_config()
    report["patient_ids"] = ["restricted-id"]
    with pytest.raises(ValueError, match="unexpected fields"):
        module.verify_report(report, config)
