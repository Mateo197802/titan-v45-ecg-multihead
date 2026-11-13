from __future__ import annotations

import json
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLOSURE = ROOT / "docs" / "reviewer_closure"


def _load(name: str) -> dict:
    return json.loads((CLOSURE / name).read_text(encoding="utf-8"))


def test_round2_source_member_hashes_and_duplicate_are_explicit():
    graph = _load("HISTORICAL_PROVENANCE_GRAPH.json")
    members = [
        member for member in graph["source_members"]
        if member["id"].startswith("SRC-") and not member["id"].startswith("SRC-REV6-")
    ]

    assert len(members) == 25
    assert len({member["id"] for member in members}) == 25
    assert Counter(member["copy"] for member in members) == {
        "BYTE_IDENTICAL_TO_RECEIPT": 14,
        "SANITIZED_SOURCE_HASH_DIFFERS": 11,
    }
    assert len({member["delivered_sha256"] for member in members}) == 24
    assert [member["id"] for member in members if "duplicate_of" in member] == ["SRC-08"]
    for member in members:
        assert len(member["source_sha256"]) == 64
        assert len(member["delivered_sha256"]) == 64
        int(member["source_sha256"], 16)
        int(member["delivered_sha256"], 16)
        if member["copy"] == "BYTE_IDENTICAL_TO_RECEIPT":
            assert member["source_sha256"] == member["delivered_sha256"]
        else:
            assert member["source_sha256"] != member["delivered_sha256"]


def test_round2_reviewer_coverage_and_statuses_are_internally_consistent():
    update = _load("REVIEWER_15_EVIDENCE_UPDATE.json")
    source = json.loads(
        subprocess.run(
            [
                "git",
                "show",
                "52ae5743f33419e3d045d4e0c9ab58d93607e90a:docs/reviewer_closure/TECHNICAL_15_EVIDENCE_CEILING_EXECUTION.json",
            ],
            check=True,
            cwd=ROOT,
            capture_output=True,
            text=True,
        ).stdout
    )
    items = update["items"]
    source_items = {item["id"]: item for item in source["reviewer_items"]}

    assert len(items) == 15
    assert len({item["id"] for item in items}) == 15
    assert update["status_counts_after"]["partially_addressed"] == 12
    assert update["status_counts_after"]["not_satisfied"] == 3
    assert update["status_counts_after"]["technical_status_reclassifications"] == 0
    assert update["status_counts_after"]["reviewer_satisfaction_reclassifications"] == 0
    assert update["rubric"]["documentary_ceiling_pct"] is None
    for item in items:
        original = source_items[item["id"]]
        assert item["technical_status_before"] == original["baseline_technical_status"]
        assert item["reviewer_satisfaction_before"] == original[
            "baseline_reviewer_satisfaction"
        ]
        assert item["technical_status_before"] == item["technical_status_after"]
        assert item["reviewer_satisfaction_before"] == item["reviewer_satisfaction_after"]
        coverage = item["subrequirements"]
        calculated = round(100 * coverage["weighted_verified"] / coverage["total"], 1)
        assert coverage["coverage_pct"] == calculated
        partial_statuses = set(update["rubric"]["partial_statuses"])
        weights = [
            1.0 if row["status"] == "VERIFIED_BOUNDED" else 0.5 if row["status"] in partial_statuses else 0.0
            for row in original["technical_subrequirement_coverage"]
        ]
        assert coverage["total"] == len(weights)
        assert coverage["weighted_verified"] == sum(weights)
        assert coverage["coverage_pct"] == round(100 * sum(weights) / len(weights), 1)
        assert item["resolved_subrequirements"] == []


def test_round2_audit_receipt_does_not_claim_private_bundle_publication():
    receipt = _load("RECOVERY_ZIP_AUDIT_ROUND2_2026-11-10.json")

    assert receipt["expected_sha256_match"] is True
    assert receipt["zip_crc_ok"] is True
    assert receipt["inventory_rows_match_bytes_and_hashes"] is True
    assert receipt["checksum_manifest_match"] is True
    assert receipt["historical_code_inventory"]["executed_recovered_code"] is False
    assert receipt["privacy_screening"]["raw_archive_or_receipts_published"] is False
    assert receipt["payload_comparison"]["pr3_byte_identical_count"] == 0
    assert receipt["payload_comparison"]["pr4_byte_identical_count"] == 0


def test_public_round2_evidence_contains_no_private_absolute_paths():
    paths = [
        CLOSURE / "HISTORICAL_PROVENANCE_GRAPH.json",
        CLOSURE / "REVIEWER_15_EVIDENCE_UPDATE.json",
        CLOSURE / "RECOVERY_ZIP_AUDIT_ROUND2_2026-11-10.json",
    ]
    content = "\n".join(path.read_text(encoding="utf-8") for path in paths).lower()

    assert "/home/" not in content
    assert "/scratch/" not in content
    assert "c:\\users\\" not in content
    assert "diego.almeida__" not in content
