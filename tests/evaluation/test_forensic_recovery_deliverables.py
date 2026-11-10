from __future__ import annotations

import json
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
