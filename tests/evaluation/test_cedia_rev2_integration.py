import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLOSURE = ROOT / "docs" / "reviewer_closure"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_cedia_addendum_preserves_reviewer_and_audit_statuses() -> None:
    addendum = read_json(CLOSURE / "REVIEWER_15_CEDIA_REV2_ADDENDUM.json")
    prior = read_json(CLOSURE / "REVIEWER_15_EVIDENCE_UPDATE.json")
    matrix = read_json(CLOSURE / "REVIEWER_48_DETAILED.json")

    prior_by_id = {item["id"]: item for item in prior["items"]}
    matrix_by_id = {item["id"]: item for item in matrix["items"]}
    assert len(addendum["items"]) == 15
    assert len(addendum["internal_audits"]) == 12
    assert addendum["summary"]["technical_status_changes"] == 0
    assert addendum["summary"]["reviewer_satisfaction_changes"] == 0
    assert addendum["summary"]["coverage_percentage_point_changes"] == 0

    for item in addendum["items"]:
        previous = prior_by_id[item["id"]]
        canonical = matrix_by_id[item["id"]]
        assert item["technical_status_before"] == item["technical_status_after"]
        assert item["reviewer_satisfaction_before"] == item["reviewer_satisfaction_after"]
        assert item["coverage_pct_before"] == item["coverage_pct_after"]
        assert item["technical_status_after"] == previous["technical_status_after"]
        assert item["reviewer_satisfaction_after"] == previous["reviewer_satisfaction_after"]
        assert item["coverage_pct_after"] == previous["subrequirements"]["coverage_pct"]
        assert item["technical_status_after"] == canonical["technical_status"]
        assert item["reviewer_satisfaction_after"] == canonical["reviewer_satisfaction"]
        assert item["id"] in matrix["supplemental_evidence"]["reviewer_ids"]

    for audit in addendum["internal_audits"]:
        canonical = matrix_by_id[audit["id"]]
        assert audit["status_before"] == audit["status_after"]
        assert audit["status_after"] == canonical["technical_status"]
        assert audit["id"] in matrix["supplemental_evidence"]["internal_audit_ids"]

    assert matrix["counts"] == {"total": 48, "peer_review": 36, "project_audit": 12}
    claim_ids = {
        claim["id"]
        for claim in read_json(CLOSURE / "HISTORICAL_RECOVERY_CANONICAL_INDEX.json")["assertions"]
    }
    for item in addendum["items"]:
        assert set(item["source_claim_ids"]) <= claim_ids
    claim_ids = {
        claim["id"]
        for claim in read_json(CLOSURE / "HISTORICAL_RECOVERY_CANONICAL_INDEX.json")["assertions"]
    }
    for item in addendum["items"]:
        assert set(item["source_claim_ids"]) <= claim_ids


def test_canonical_index_and_graph_keep_cedia_claims_bounded() -> None:
    index = read_json(CLOSURE / "HISTORICAL_RECOVERY_CANONICAL_INDEX.json")
    graph = read_json(CLOSURE / "HISTORICAL_PROVENANCE_GRAPH.json")
    claim_ids = {claim["id"] for claim in index["assertions"]}

    assert index["pull_requests"]["pr3"]["head"] == graph["pr3_head_audited"]
    assert graph["pr4_head_audited"] == index["pull_requests"]["pr4"]["head"]
    assert graph["pr5_used"] is False
    assert graph["pr4_modified"] is True
    assert graph["pr4_modified_before_rev3_rev6_integration"] is False
    assert graph["pr5_modified"] is False
    assert {
        "CEDIA-ASSERT-PLAN-LINEAGE",
        "CEDIA-ASSERT-PLAN-AE-INPUT-DIGESTS",
        "CEDIA-ASSERT-PLAN-AF-REPORTED-OUTPUTS",
        "CEDIA-ASSERT-SPLIT-CACHE-KEYS",
        "CEDIA-ASSERT-AUXILIARY-CACHE-SUPPORT",
        "CEDIA-ASSERT-LOADER-CANDIDATE",
        "CEDIA-ASSERT-OPTUNA-41M",
        "CEDIA-ASSERT-BACKBONE-HASH-CORROBORATION",
    } <= claim_ids
    v3c_claim = next(
        claim
        for claim in index["assertions"]
        if claim["id"] == "CEDIA-ASSERT-V3C-TRIAL6-CORROBORATION"
    )
    assert v3c_claim["classification"] == "DUPLICATED_EVIDENCE"
    assert v3c_claim["trial_snapshot"]["rows"] == 9
    assert v3c_claim["trial_snapshot"]["planned_trials"] == 12
    assert v3c_claim["new_source_artifacts"] == 0
    assert v3c_claim["lineage_completion"] is False
    af_summary = next(
        claim for claim in index["assertions"] if claim["id"] == "CEDIA-ASSERT-PLAN-AF-REPORTED-OUTPUTS"
    )
    assert af_summary["reported_metrics"]["handoff_rows"] == 23
    assert af_summary["reported_metrics"]["valid_for_gate"] == 0
    assert af_summary["quarantine_denominator"] is None
    assert af_summary["quarantine_rate"] is None
    assert af_summary["metrics_recomputed_from_per_record_predictions"] is False

    rev2_inventory = index["exported_inventory_summary"]["rev2"]
    assert rev2_inventory["row_count"] == 145
    assert rev2_inventory["duplicate_hash_groups"] == 3
    assert rev2_inventory["duplicate_extra_rows"] == 3
    assert rev2_inventory["source_hashes_recomputed_from_original_cedia_bytes"] is False
    assert index["reconciliation_counts"]["new_verified_originals_linked_to_v45_execution"] == 0
    assert index["reconciliation_counts"]["new_supported_but_unverified_links"] == 5
    assert index["reconciliation_counts"]["new_derived_checks"] == 1
    assert index["reconciliation_counts"]["corroborates_existing_evidence"] == 3
    assert index["reconciliation_counts"]["duplicated_evidence_records"] == 1
    assert index["reconciliation_counts"]["scientific_contradictions_newly_resolved"] == 0
    assertion_classes = Counter(item["classification"] for item in index["assertions"])
    assert assertion_classes["NEW_SUPPORTED_BUT_UNVERIFIED_LINK"] == 5
    assert assertion_classes["CORROBORATES_EXISTING_EVIDENCE"] == 3
    assert assertion_classes["DUPLICATED_EVIDENCE"] == 1
    assert len(index["assertions"]) == 9
    complete_comparison = index["byte_comparisons"][
        "complete_recovery_against_current_pr3_git_tree"
    ]
    directed_comparison = index["byte_comparisons"][
        "directed2_recovery_against_current_pr3_git_tree"
    ]
    assert complete_comparison["tracked_files_compared"] == 583
    assert complete_comparison["byte_identical_payloads"] == 11
    assert complete_comparison["exact_relative_path_and_bytes"] == 0
    assert directed_comparison["byte_identical_payloads"] == 0

    jobs = {job["id"]: job for job in graph["job_observations"]}
    assert jobs["JOB-15874-15905"]["afterok_edges_within_chain"] == 0
    assert jobs["JOB-15874-15905"]["input_consumption_verified"] is False
    af = next(edge for edge in graph["edges"] if edge["from"] == "JOB-15903-15905" and edge["to"] == "V45-QUARANTINE")
    assert af["status"] == "NOT_LINKED"
    v3c_edge = next(
        edge
        for edge in graph["edges"]
        if edge["from"] == "PKG-CEDIA-REV2-20261110" and edge["to"] == "JOB-16781"
    )
    assert v3c_edge["status"] == "DUPLICATED_EVIDENCE"

    index_text = (CLOSURE / "HISTORICAL_RECOVERY_CANONICAL_INDEX.md").read_text(encoding="utf-8")
    for forbidden in ("/home/diego.almeida", "Mateo Gavilanes/V4.5_CEDIA", "record_id,patient_id"):
        assert forbidden not in index_text


def test_public_recovery_documents_exclude_private_paths_and_row_identifiers() -> None:
    public_docs = (
        CLOSURE / "HISTORICAL_RECOVERY_CANONICAL_INDEX.json",
        CLOSURE / "HISTORICAL_RECOVERY_CANONICAL_INDEX.md",
        CLOSURE / "HISTORICAL_PROVENANCE_GRAPH.json",
        CLOSURE / "HISTORICAL_PROVENANCE_GRAPH.md",
        CLOSURE / "REVIEWER_15_CEDIA_REV2_ADDENDUM.json",
        CLOSURE / "REVIEWER_15_CEDIA_REV2_ADDENDUM.md",
        CLOSURE / "PLAN_AE_AF_QUARANTINE_EVIDENCE.md",
        CLOSURE / "OPTUNA_PR4_EVIDENCE_HANDOFF.md",
    )
    forbidden_paths = ("/home/diego.almeida", "Mateo Gavilanes/V4.5_CEDIA")
    identifier_field = re.compile(r'"(?:patient|record|ecg)_id"\s*:', re.IGNORECASE)

    for path in public_docs:
        text = path.read_text(encoding="utf-8")
        assert not any(value in text for value in forbidden_paths), path.name
        assert identifier_field.search(text) is None, path.name


def test_legacy_v4_recomputation_remains_separate_from_v45_quarantine() -> None:
    receipt = read_json(
        CLOSURE / "receipts" / "LEGACY_V4_QUARANTINE_RECOMPUTATION_2026-11-10.json"
    )
    graph = read_json(CLOSURE / "HISTORICAL_PROVENANCE_GRAPH.json")
    matrix = read_json(CLOSURE / "REVIEWER_48_DETAILED.json")
    matrix_by_id = {item["id"]: item for item in matrix["items"]}

    assert receipt["source_scope"] == "V4 May 2026 legacy Primary-9 diagnostic; not V4.5 June"
    assert receipt["primary9"]["records"] == 672
    assert receipt["primary9"]["correct_diagonal"] == 461
    assert receipt["primary9"]["off_diagonal_errors"] == 211
    assert receipt["routing_on_error_subset_only"]["accepted_prediction"] == 107
    assert receipt["routing_on_error_subset_only"]["records"] == 211
    assert receipt["routing_on_error_subset_only"]["full_672_record_quarantine_rate"] is None
    assert next(node for node in graph["artifact_nodes"] if node["id"] == "V4-MAY-LEGACY-QUARANTINE")["status"] == "VERIFIED_AS_DIFFERENT_MODEL_VERSION"
    legacy_edge = next(
        edge
        for edge in graph["edges"]
        if edge["from"] == "V4-MAY-LEGACY-QUARANTINE" and edge["to"] == "V45-QUARANTINE"
    )
    assert legacy_edge["status"] == "WRONG_MODEL_VERSION"
    for reviewer_id in ("R1-2", "R2-4k"):
        assert "docs/reviewer_closure/V4_LEGACY_QUARANTINE_DISPOSITION.md" in matrix_by_id[reviewer_id]["evidence"]
        assert "docs/reviewer_closure/receipts/LEGACY_V4_QUARANTINE_RECOMPUTATION_2026-11-10.json" in matrix_by_id[reviewer_id]["evidence"]
    index_check = read_json(
        CLOSURE / "HISTORICAL_RECOVERY_CANONICAL_INDEX.json"
    )["derived_verifications"][0]
    assert index_check["classification"] == "NEW_DERIVED_CHECK"
    assert index_check["receipt_reproduced"] is True
    assert index_check["result"]["full_population_quarantine_rate"] is None
    assert matrix["supplemental_evidence"]["legacy_v4_may_recheck"]["status_changes"] == 0
