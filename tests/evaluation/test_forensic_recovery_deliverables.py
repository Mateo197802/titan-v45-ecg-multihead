from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs/reviewer_closure"
REQUIRED_DOCUMENTS = (
    "EVIDENCE_SOURCE_TRIAGE.md",
    "RECOVERED_VS_MISSING_HISTORICAL_EVIDENCE.md",
    "CHECKPOINT_TO_PATIENT_SPLIT_LINEAGE.md",
    "HISTORICAL_LOADER_IDENTITY_AND_REPLAY.md",
    "OTHER_AUX_ROUTING_AND_QUARANTINE_PROVENANCE.md",
    "CUSTODIAN_BACKUP_REQUEST.md",
)


def test_forensic_recovery_deliverables_exist_and_are_sanitized():
    for name in REQUIRED_DOCUMENTS:
        assert (DOCS / name).is_file(), name

    documents = "\n".join(
        (DOCS / name).read_text(encoding="utf-8") for name in REQUIRED_DOCUMENTS
    )
    assert "17314" in documents
    assert "17315" in documents
    assert "1,564/1,643" in documents
    assert "0.951917" in documents
    assert "0.800938" in documents
    assert "1f0b29540c84cb68a5719e74e02ce3c58a1a4c38da66a8b39c9862913d2b18e8" in documents
    assert "19df83ca78f0688a99e06a967611e04b4f308d0fd5a1af8df1bdd3efe144452e" in documents
    assert "/home/diego." not in documents
    assert "C:\\Users\\" not in documents


def test_reviewer_matrix_links_the_new_p6_selection_evidence():
    matrix = json.loads(
        (DOCS / "REVIEWER_48_DETAILED.json").read_text(encoding="utf-8")
    )
    items = {item["id"]: item for item in matrix["items"]}
    assert "docs/reviewer_closure/CHECKPOINT_TO_PATIENT_SPLIT_LINEAGE.md" in items[
        "R1-1"
    ]["evidence"]
    assert "17314" in items["R1-1"]["protocol_population_result"]
    assert "17314" in items["R1-1"]["unresolved"]


def test_cedia_cleanup_manifest_receipt_is_bounded_and_sanitized():
    receipt_path = DOCS / "receipts/CEDIA_CLEANUP_MANIFEST_TRIAGE_2026-11-10.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    assert receipt["schema"] == "TITAN_V45_CEDIA_CLEANUP_MANIFEST_TRIAGE_V1"
    manifest = receipt["manifest"]
    assert manifest["bytes"] == 225427
    assert re.fullmatch(r"[0-9a-f]{64}", manifest["sha256"])
    assert manifest["candidate_count"] == 1438
    assert manifest["per_entry_sha256_present"] is False
    assert manifest["per_entry_mtime_present"] is False
    assert manifest["embedded_confirmation_digest_matches_file"] is False
    assert manifest["embedded_confirmation_digest_semantics_verified"] is False

    optuna = receipt["optuna_inventory"]
    assert len(optuna["nonempty_logs_listed"]) == 3
    assert len(optuna["zero_byte_error_logs_listed"]) == 3
    assert optuna["database_listed"] is False
    assert receipt["bounded_search"]["directory_count"] == 4914
    assert receipt["bounded_search"]["stage_archive_optuna_name_hits"] == 0
    assert receipt["bounded_search"]["archive_extracted"] is False
    target_search = receipt["historical_target_name_search"]
    assert target_search["exact_target_match_count"] == 0
    assert target_search["term_entry_counts"] == {
        "v3h": 0,
        "v3s": 0,
        "v3m": 0,
        "v3p": 0,
        "loader": 0,
        "quarantine": 0,
        "split90": 0,
        "split10": 0,
        "panel_index": 0,
        "optuna": 6,
        "sqlite": 0,
        "manifest": 0,
    }

    public_text = json.dumps(receipt)
    assert "/home/diego." not in public_text
    assert "C:\\Users\\" not in public_text
    assert "legacy_root" not in public_text
    assert "patient_id" not in public_text

    matrix = json.loads((DOCS / "REVIEWER_48_DETAILED.json").read_text(encoding="utf-8"))
    audit = next(item for item in matrix["items"] if item["id"] == "A-06")
    assert receipt_path.relative_to(ROOT).as_posix() in audit["evidence"]
