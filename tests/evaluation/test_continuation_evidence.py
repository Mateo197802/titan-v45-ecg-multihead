from __future__ import annotations

import hashlib
import json
from pathlib import Path

from titan_v45.evaluation.decision_policy import audit_saved_membership_policy
from titan_v45.evaluation.source_checksums import audit_source_checksums

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "outputs/results/revision_20261029"


def test_export_hashes_and_privacy_boundaries() -> None:
    receipt = json.loads((RESULTS / "integrity.json").read_text())
    for name, expected in receipt["outputs_sha256"].items():
        raw = (RESULTS / name).read_bytes().replace(b"\r\n", b"\n")
        assert hashlib.sha256(raw).hexdigest() == expected, name
        assert not any(token in raw for token in [b"/home/", b"C:\\Users", b'"patient_id"', b'"header"'])


def test_exact_header_mismatch_does_not_override_signal_provenance() -> None:
    report, details = audit_source_checksums(RESULTS / "data_test_file_fingerprints.json", RESULTS / "official_checksums_selected.txt")
    assert report["records_total"] == 84
    assert report["record_status_counts"] == {"signal_only": 84}
    assert not report["all_records_fully_verified"]
    assert not report["independent_validation"]
    assert all(row["header_status"] == "mismatch" for row in details)
    summary = json.loads((RESULTS / "data_test_provenance_summary.json").read_text())
    assert summary["source_counts"] == {"cpsc_2018": 3, "georgia": 5, "ptb-xl": 76}
    assert summary["header_signal_contract_equal"] == summary["header_diagnosis_codes_equal"] == 84
    assert summary["archive_reconciliation"]["all_hashes_match"]
    assert not summary["distribution_hold_lifted"]


def test_saved_policy_receipt_equals_live_saved_field_reconstruction() -> None:
    actual = audit_saved_membership_policy(ROOT)
    declared = json.loads((RESULTS / "membership_policy_reconstruction.json").read_text())
    assert actual == declared
    assert actual["all_decisions_reconstructed"]
    assert actual["records"] == 2193 and actual["fallback_records"] == 58
