from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "outputs/results/benchmarkmax/sph_scale_sensitivity_32761.json"
EXPERIMENT_COMMIT = "a2353f0863f05e4b1ea844f9b0c4dd4e270a6c85"
spec = importlib.util.spec_from_file_location(
    "verify_scale", ROOT / "scripts/benchmarkmax/verify_sph_scale_sensitivity.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def load_report():
    return json.loads(REPORT.read_text(encoding="utf-8"))


def test_completed_scale_receipt_is_aggregate_and_reconciles():
    summary = module.validate_report(
        load_report(), expected_job_id="32761", expected_experiment_commit=EXPERIMENT_COMMIT
    )

    assert summary == {"job_id": "32761", "records": 128, "profiles": ["P4", "P6", "P8"]}


def test_scale_receipt_rejects_private_record_fields():
    report = copy.deepcopy(load_report())
    report["record_id"] = "private"

    with pytest.raises(ValueError, match="record-level"):
        module.validate_report(
            report, expected_job_id="32761", expected_experiment_commit=EXPERIMENT_COMMIT
        )


def test_scale_receipt_rejects_changed_frozen_inputs():
    report = copy.deepcopy(load_report())
    report["frozen_ledger_sha256"] = "0" * 64

    with pytest.raises(ValueError, match="ledger hash"):
        module.validate_report(
            report, expected_job_id="32761", expected_experiment_commit=EXPERIMENT_COMMIT
        )
