from __future__ import annotations

import json
import math
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLOSURE = ROOT / "docs/reviewer_closure"
BASE_HEAD = "52ae5743f33419e3d045d4e0c9ab58d93607e90a"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_rev3_rev6_receipt_and_graph_are_integrity_pinned() -> None:
    receipt = read_json(CLOSURE / "receipts/CEDIA_REV3_REV6_PACKAGE_AUDIT_2026-11-11.json")
    graph = read_json(CLOSURE / "HISTORICAL_PROVENANCE_GRAPH.json")
    assert receipt["valid"] is True
    assert receipt["recovered_code_executed"] is False
    expected = {
        3: "1975a1bbc65a004b444676e7627349e43d9516898215a3b5ecbf242539c9c986",
        4: "3a87a980c76c1602f450e1aaab720245b566aee4807c21e3f779b73c0469b77a",
        5: "0e88146b007f68feba2ff643f6d98126d139f19d37fe395931bd640453005773",
        6: "4bf835059dfdf40f7fd4b0c1879d94b1175efcb091f6cf9065a5e482a3ad2b11",
    }
    package_rows = {row["revision"]: row for row in receipt["packages"]}
    assert {revision: row["archive_sha256"] for revision, row in package_rows.items()} == expected
    assert all(row["valid"] and row["crc_ok"] for row in package_rows.values())

    source_rows = {row["id"]: row for row in graph["source_members"] if row["id"].startswith("SRC-REV6-")}
    source_hashes = {
        item["member"].replace("codigo_archivo_fuentes/", ""): item["sha256"]
        for item in package_rows[6]["source_code_members"]
    }
    assert len(source_rows) == 10
    assert len({row["delivered_sha256"] for row in source_rows.values()}) == 10
    assert all(row["source_bytes_reauthenticated"] is False for row in source_rows.values())
    assert sum(row["copy"] == "NEW_CONTENT_VS_TRACKED_PR3_TREE" for row in source_rows.values()) == 9
    assert sum(row["copy"] == "DUPLICATE_OF_TRACKED_CANDIDATE" for row in source_rows.values()) == 1
    assert all(row["job_link"] == "UNVERIFIED" for row in source_rows.values())
    assert {row["name"]: row["delivered_sha256"] for row in source_rows.values()} == source_hashes

    edge_pairs = [(edge["from"], edge["to"]) for edge in graph["edges"]]
    assert len(edge_pairs) == len(set(edge_pairs))
    assert next(
        edge for edge in graph["edges"]
        if edge["from"] == "CKPT-V3F-RELEASE" and edge["to"] == "JOB-16781"
    )["status"] == "PATH_REFERENCE_ONLY"
    assert next(
        edge for edge in graph["edges"]
        if edge["from"] == "JOB-16781" and edge["to"] == "CKPT-V3F-RELEASE"
    )["status"] == "UNVERIFIED"
    assert graph["rev3_rev6_integration"]["new_originals_linked_to_v45_jobs_and_checkpoints"] == 0


def test_rev3_rev6_coverage_recalculates_without_satisfaction_upgrade() -> None:
    previous = read_json(CLOSURE / "REVIEWER_15_EVIDENCE_UPDATE.json")
    current = read_json(CLOSURE / "REVIEWER_15_COVERAGE_AND_CEILING.json")
    technical = read_json(CLOSURE / "TECHNICAL_15_EVIDENCE_CEILING_EXECUTION.json")
    matrix = read_json(CLOSURE / "REVIEWER_48_DETAILED.json")

    prior_points = sum(item["subrequirements"]["weighted_verified"] for item in previous["items"])
    prior_rows = sum(item["subrequirements"]["total"] for item in previous["items"])
    assert prior_points == 18.5
    assert prior_rows == 40

    current_rows = {item["id"]: item for item in current["items"]}
    assert current["aggregate"]["previous_weighted_points"] == prior_points
    assert current["aggregate"]["new_weighted_points"] == 19.5
    assert current["aggregate"]["new_subrequirements"] == prior_rows
    assert math.isclose(current["aggregate"]["new_coverage_pct"], 100 * 19.5 / 40)
    for item_id in ("R2-3c", "R2-3d"):
        row = current_rows[item_id]
        assert row["delta_pp"] == 16.7
        assert row["satisfaction"] == ("PARTIALLY_ADDRESSED" if item_id == "R2-3c" else "NOT_SATISFIED")
    assert current["aggregate"]["peer_comments_satisfied"] == 0
    assert current["aggregate"]["peer_comments_partially_addressed"] == 12
    assert current["aggregate"]["peer_comments_not_satisfied"] == 3
    assert technical["rev3_rev6_addendum"]["reviewer_satisfaction_changes"] == 0
    assert technical["rev3_rev6_addendum"]["new_v45_originals_linked_to_job_and_checkpoint"] == 0
    assert matrix["counts"] == {"total": 48, "peer_review": 36, "project_audit": 12}

    base_json = subprocess.run(
        ["git", "show", f"{BASE_HEAD}:docs/reviewer_closure/REVIEWER_48_DETAILED.json"],
        check=True,
        cwd=ROOT,
        capture_output=True,
        text=True,
    ).stdout
    baseline_items = json.loads(base_json)["items"]
    editorial_before = {
        item["id"]: item for item in baseline_items
        if item["reviewer_satisfaction"] == "EDITORIAL_ACTION_ONLY"
    }
    editorial_now = {
        item["id"]: item for item in matrix["items"]
        if item["reviewer_satisfaction"] == "EDITORIAL_ACTION_ONLY"
    }
    assert len(editorial_before) == 21
    assert editorial_now == editorial_before


def test_rev3_rev6_public_documents_are_sanitized_and_rendered() -> None:
    source = read_json(CLOSURE / "REVIEWER_48_DETAILED.json")
    report = read_json(CLOSURE / "TECHNICAL_15_EVIDENCE_CEILING_EXECUTION.json")
    rendered = (CLOSURE / "REVIEWER_48_DETAILED.md").read_text(encoding="utf-8")
    assert source["supplemental_evidence"]["rev3_rev6_addendum"]["status_changes"] == 0
    assert "Supplemental CEDIA REV3-REV6 Evidence" in rendered
    assert "static source semantics" in rendered.lower()
    assert report["current_matrix_sha256"] == __import__("hashlib").sha256(
        (CLOSURE / "REVIEWER_48_DETAILED.json").read_bytes()
    ).hexdigest()

    public_paths = [
        CLOSURE / "CEDIA_FINAL_RECOVERY_REPORT.md",
        CLOSURE / "CEDIA_SOURCE_CODE_AUTHENTICATION.md",
        CLOSURE / "HISTORICAL_PROVENANCE_GRAPH.json",
        CLOSURE / "HISTORICAL_PROVENANCE_GRAPH.md",
        CLOSURE / "HISTORICAL_RECOVERY_CANONICAL_INDEX.json",
        CLOSURE / "HISTORICAL_RECOVERY_CANONICAL_INDEX.md",
        CLOSURE / "REVIEWER_15_COVERAGE_AND_CEILING.json",
        CLOSURE / "REVIEWER_15_COVERAGE_AND_CEILING.md",
        CLOSURE / "receipts/CEDIA_TARGETED_RECOVERY_SEARCH_2026-11-11.json",
    ]
    for path in public_paths:
        text = path.read_text(encoding="utf-8")
        assert "/home/diego." not in text
        assert "Mateo Gavilanes/V4.5_CEDIA" not in text
        assert not re.search(r'"(?:patient|record|ecg)_id"\s*:', text, re.I)


def test_targeted_cedia_search_is_bounded_and_does_not_change_coverage() -> None:
    receipt = read_json(CLOSURE / "receipts/CEDIA_TARGETED_RECOVERY_SEARCH_2026-11-11.json")
    matrix = read_json(CLOSURE / "REVIEWER_48_DETAILED.json")
    coverage = read_json(CLOSURE / "REVIEWER_15_COVERAGE_AND_CEILING.json")

    assert receipt["remote_host_verified"] is True
    assert receipt["authorized_account_home_confirmed"] is True
    assert all(scope["matches"] == 0 for scope in receipt["scopes"])
    project_scope = next(scope for scope in receipt["scopes"] if scope["scope_id"] == "AUTHORIZED_V45_PROJECT_ROOT")
    assert any("13169" in pattern and "16748-16759" in pattern for pattern in project_scope["patterns"])
    assert receipt["search_execution"]["broad_home_traversal"] == "INTERRUPTED_AND_EXCLUDED_FROM_EVIDENCE"
    assert receipt["search_execution"]["archive_contents_inspected"] is False
    assert receipt["search_execution"]["clinical_data_read"] is False
    assert receipt["status_or_coverage_change"] is False
    assert matrix["supplemental_evidence"]["rev3_rev6_addendum"]["status_changes"] == 0
    assert coverage["aggregate"]["global_status_changes"] == 0
