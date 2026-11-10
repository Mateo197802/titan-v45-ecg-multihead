from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from titan_v45.evaluation.release_evidence import _sha256_lf_normalized

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs/reviewer_closure"
REPORT = DOCS / "TECHNICAL_15_EVIDENCE_CEILING_EXECUTION.json"
EXPECTED_IDS = {
    "R1-1",
    "R1-2",
    "R1-3",
    "R1-4",
    "R2-general",
    "R2-2b",
    "R2-3a",
    "R2-3c",
    "R2-3d",
    "R2-3e",
    "R2-3f",
    "R2-4a",
    "R2-4e",
    "R2-4k",
    "R2-5",
}
REQUIRED_ROW_FIELDS = {
    "id",
    "request",
    "baseline_technical_status",
    "baseline_reviewer_satisfaction",
    "technical_subrequirement_coverage",
    "scientific_evidence_status",
    "historical_provenance_status",
    "editorial_status",
    "evidence_recovered_or_verified",
    "what_this_does_not_prove",
    "recoverability",
    "remaining_action",
    "unverified_claims",
}


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _nested_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key.lower()
            yield from _nested_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _nested_keys(child)


def test_execution_register_covers_the_15_technical_reviewer_items_without_relabeling():
    report = _load_json(REPORT)
    matrix_path = DOCS / "REVIEWER_48_DETAILED.json"
    matrix = _load_json(matrix_path)
    matrix_by_id = {item["id"]: item for item in matrix["items"]}
    rows = report["reviewer_items"]
    rows_by_id = {row["id"]: row for row in rows}

    assert report["schema"] == "TITAN_V45_TECHNICAL_15_EVIDENCE_EXECUTION_V1"
    assert report["baseline_matrix_sha256"] == hashlib.sha256(
        matrix_path.read_bytes()
    ).hexdigest()
    assert len(rows) == 15
    assert set(rows_by_id) == EXPECTED_IDS
    assert report["matrix_counts"] == {
        "peer_review_total": 36,
        "project_audits_total": 12,
        "technical_peer_review_items_in_this_register": 15,
        "editorial_only_peer_review_items_unchanged": 21,
    }
    editorial_items = [
        item for item in matrix["items"]
        if item["reviewer_satisfaction"] == "EDITORIAL_ACTION_ONLY"
    ]
    assert len(editorial_items) == 21

    for item_id, row in rows_by_id.items():
        source = matrix_by_id[item_id]
        assert REQUIRED_ROW_FIELDS <= row.keys(), item_id
        assert row["request"] == source["request"]
        assert row["baseline_technical_status"] == source["technical_status"]
        assert row["baseline_reviewer_satisfaction"] == source["reviewer_satisfaction"]
        assert row["editorial_status"] == "SIN_EDITAR"
        assert row["technical_subrequirement_coverage"]
        assert row["remaining_action"]

    width_finding = next(
        item for item in rows_by_id["R2-3f"]["technical_subrequirement_coverage"]
        if item["requirement"] == "Specialist hidden-width metadata"
    )
    assert width_finding["status"] == "CHECKPOINT_METADATA_MISMATCH_RECORDED"
    assert "192" in width_finding["boundary"] and "512" in width_finding["boundary"]

    audits = report["project_audit_snapshot"]
    assert len(audits) == 12
    assert {row["id"] for row in audits} == {f"A-{n:02d}" for n in range(1, 13)}
    for audit in audits:
        source = matrix_by_id[audit["id"]]
        assert audit["technical_status"] == source["technical_status"]
        assert audit["reviewer_satisfaction"] == "NOT_APPLICABLE_AUDIT"

    for fingerprint in report["artifact_fingerprints"]:
        path = ROOT / fingerprint["path"]
        assert path.is_file(), fingerprint["path"]
        assert path.stat().st_size == fingerprint["bytes"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == fingerprint["sha256"]


def test_execution_receipts_are_aggregate_only_and_hash_pinned():
    report = _load_json(REPORT)
    receipts = report["execution_receipts"]
    reproduction_doc = (DOCS / "REPRODUCIBILITY_VERIFICATION_RECEIPTS.md").read_text(
        encoding="utf-8"
    )
    assert {item["id"] for item in receipts} == {
        "AF_REFERENCE_RECHECK",
        "RELEASE_METRICS_RECOMPUTE",
        "SPH_AGGREGATE_VALIDATION",
    }
    for receipt in receipts:
        path = ROOT / receipt["path"]
        assert path.is_file(), receipt["path"]
        assert receipt["sha256_basis"] == "UTF-8 text with CRLF normalized to LF"
        assert _sha256_lf_normalized(path) == receipt["sha256"]
        assert receipt["sha256"] in reproduction_doc
        data = _load_json(path)
        keys = set(_nested_keys(data))
        assert not any(
            marker in key
            for key in keys
            for marker in ("record_id", "patient_id", "sample_id", "per_record")
        )
        serialized = path.read_text(encoding="utf-8")
        assert "/home/diego." not in serialized
        assert "C:\\Users\\" not in serialized


def test_execution_documents_link_the_register_and_keep_external_limits_explicit():
    report_path = "TECHNICAL_15_EVIDENCE_CEILING_EXECUTION.json"
    markdown = (DOCS / "TECHNICAL_15_EVIDENCE_CEILING_EXECUTION.md").read_text(
        encoding="utf-8"
    )
    for item_id in sorted(EXPECTED_IDS):
        assert f"### {item_id}" in markdown
    assert "PATIENT_ISOLATION_NOT_CERTIFIED" in markdown
    assert "not assessed" in markdown.lower()
    assert "not an independent clinical validation" in markdown.lower()
    assert (DOCS / report_path).is_file()
    for name in (
        "CHECKPOINT_MANIFEST_JOB_EDGE_VERIFICATION.md",
        "GENERALIZATION_AND_COHORT_INDEPENDENCE_AUDIT.md",
        "FULL_CLASS_COVERAGE_AND_ROUTING_AUDIT.md",
        "QUARANTINE_HISTORICAL_VS_PROSPECTIVE.md",
        "REPRODUCIBILITY_VERIFICATION_RECEIPTS.md",
    ):
        assert (DOCS / name).is_file(), name

    markdown_paths = [
        DOCS / "TECHNICAL_15_EVIDENCE_CEILING_EXECUTION.md",
        DOCS / "CHECKPOINT_MANIFEST_JOB_EDGE_VERIFICATION.md",
        DOCS / "GENERALIZATION_AND_COHORT_INDEPENDENCE_AUDIT.md",
        DOCS / "FULL_CLASS_COVERAGE_AND_ROUTING_AUDIT.md",
        DOCS / "QUARANTINE_HISTORICAL_VS_PROSPECTIVE.md",
        DOCS / "REPRODUCIBILITY_VERIFICATION_RECEIPTS.md",
        DOCS / "REVIEWER_CODE_AND_FORMULA_AUDIT.md",
    ]
    for source_path in markdown_paths:
        links = re.findall(r"\]\(([^)]+)\)", source_path.read_text(encoding="utf-8"))
        for link in links:
            target = link.split("#", 1)[0]
            if target.startswith(("http://", "https://")):
                continue
            assert (source_path.parent / target).is_file(), f"{source_path.name}: {link}"


def test_new_closure_documents_do_not_export_private_paths_or_row_identifiers():
    paths = [
        DOCS / "TECHNICAL_15_EVIDENCE_CEILING_EXECUTION.md",
        DOCS / "TECHNICAL_15_EVIDENCE_CEILING_EXECUTION.json",
        DOCS / "CHECKPOINT_MANIFEST_JOB_EDGE_VERIFICATION.md",
        DOCS / "GENERALIZATION_AND_COHORT_INDEPENDENCE_AUDIT.md",
        DOCS / "FULL_CLASS_COVERAGE_AND_ROUTING_AUDIT.md",
        DOCS / "QUARANTINE_HISTORICAL_VS_PROSPECTIVE.md",
        DOCS / "REPRODUCIBILITY_VERIFICATION_RECEIPTS.md",
        DOCS / "receipts/AF_REFERENCE_RECHECK_2026-11-10.json",
        DOCS / "receipts/RELEASE_METRICS_RECHECK_2026-11-10.json",
        DOCS / "receipts/SPH_AGGREGATE_VALIDATION_2026-11-10.json",
    ]
    for path in paths:
        content = path.read_text(encoding="utf-8")
        assert "/home/diego." not in content
        assert "C:\\Users\\" not in content
        assert not re.search(r"\b(?:record_id|patient_id|sample_id)\s*[:=]", content, re.I)
