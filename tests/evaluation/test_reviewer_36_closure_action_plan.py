from __future__ import annotations

import json
import re
from collections import Counter
from copy import deepcopy
from pathlib import Path

import pytest

from scripts.evaluation.export_reviewer_proposed_tables import load_inputs, render_tables

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs/reviewer_closure"
SOURCE = DOCS / "REVIEWER_48_DETAILED.json"
PLAN_JSON = DOCS / "REVIEWER_36_CLOSURE_ACTION_PLAN.json"
PLAN_MD = DOCS / "REVIEWER_36_CLOSURE_ACTION_PLAN.md"
TECHNICAL_DRAFTS = (
    "REVIEWER_REPRODUCIBILITY_GAPS.md",
    "REVIEWER_CODE_AND_FORMULA_AUDIT.md",
    "REVIEWER_FIGURE_TABLE_CORRECTIONS.md",
    "REVIEWER_CLAIM_WITHDRAWAL_DECISIONS.md",
    "REVIEWER_RESPONSE_EVIDENCE_DRAFT.md",
    "REVIEWER_PROPOSED_TABLES.md",
)
PUBLIC_REVIEWER_ARTIFACTS = (
    ROOT / "docs/README.md",
    DOCS / "EVIDENCE_SOURCE_TRIAGE.md",
    DOCS / "REVIEWER_36_CLOSURE_ACTION_PLAN.json",
    DOCS / "REVIEWER_36_CLOSURE_ACTION_PLAN.md",
    *(DOCS / name for name in TECHNICAL_DRAFTS),
)


def test_action_plan_preserves_all_36_reviewer_records_and_separates_12_audits():
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    plan = json.loads(PLAN_JSON.read_text(encoding="utf-8"))
    reviewer_source = [row for row in source["items"] if not row["id"].startswith("A-")]
    audit_ids = sorted(row["id"] for row in source["items"] if row["id"].startswith("A-"))

    assert plan["schema"] == "TITAN_V45_REVIEWER_36_CLOSURE_ACTION_PLAN_V1"
    assert plan["counts"]["reviewer_comments"] == 36
    assert plan["counts"]["internal_audits_linked_not_duplicated"] == 12
    assert len(plan["items"]) == 36
    assert plan["internal_audit_ids"] == audit_ids
    assert [item["id"] for item in plan["items"]] == [
        item["id"] for item in reviewer_source
    ]
    assert plan["counts"]["reviewer_satisfaction"] == dict(
        sorted(Counter(row["reviewer_satisfaction"] for row in reviewer_source).items())
    )
    assert plan["counts"]["technical_status"] == dict(
        sorted(Counter(row["technical_status"] for row in reviewer_source).items())
    )

    required = {
        "source_record",
        "traceability",
        "evidence_confidence",
        "work_required",
        "remaining_actions",
        "manuscript_state",
    }
    for item, source_item in zip(plan["items"], reviewer_source, strict=True):
        assert required <= item.keys(), item["id"]
        assert item["source_record"] == source_item, item["id"]
        assert item["traceability"]["evidence_refs"] == source_item["evidence"]
        assert item["manuscript_state"] == "SIN_EDITAR", item["id"]
        assert item["work_required"]["targeted_recovery"] == source_item["recovery_assessment"]
        assert item["work_required"]["new_experiment"] == source_item["experiment_requirement"]
        assert item["work_required"]["manuscript_edit"] == source_item["editorial_action"]
        assert item["remaining_actions"]["recovery"] == source_item["recovery_assessment"]
        assert item["remaining_actions"]["experiment"] == source_item["experiment_requirement"]
        assert item["remaining_actions"]["editorial"] == source_item["editorial_action"]


def test_markdown_has_one_individualized_section_per_reviewer_and_no_private_paths():
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    reviewer_ids = [row["id"] for row in source["items"] if not row["id"].startswith("A-")]
    markdown = PLAN_MD.read_text(encoding="utf-8")

    for reviewer_id in reviewer_ids:
        assert markdown.count(f"### {reviewer_id} ") == 1
    assert "12 internal audits" in markdown
    assert "SIN_EDITAR" in markdown
    assert "/home/diego." not in markdown
    assert not re.search(r"[A-Za-z]:\\Users\\", markdown)


def test_action_plan_does_not_claim_satisfaction_from_ci_or_documentation_alone():
    plan = json.loads(PLAN_JSON.read_text(encoding="utf-8"))
    source_by_id = {
        item["id"]: item
        for item in json.loads(SOURCE.read_text(encoding="utf-8"))["items"]
    }

    for item in plan["items"]:
        source_item = source_by_id[item["id"]]
        assert item["reviewer_satisfaction"] == source_item["reviewer_satisfaction"]
        assert item["technical_status"] == source_item["technical_status"]
        if source_item["reviewer_satisfaction"] != "FULLY_ADDRESSED_BY_EVIDENCE":
            assert item["closure_basis"] != "CI_ONLY"
            assert item["closure_basis"] != "DOCUMENTATION_ONLY"


def test_technical_and_editorial_drafts_keep_the_documented_scientific_boundaries():
    drafts = {
        name: (DOCS / name).read_text(encoding="utf-8") for name in TECHNICAL_DRAFTS
    }
    for name in TECHNICAL_DRAFTS:
        assert name in (DOCS / "REVIEWER_36_CLOSURE_ACTION_PLAN.md").read_text(encoding="utf-8")

    reproducibility = drafts[TECHNICAL_DRAFTS[0]]
    assert "0.0006194115" in reproducibility
    assert "1e-5" in reproducibility
    assert "PATIENT_ISOLATION_NOT_CERTIFIED" in reproducibility

    formulas = drafts[TECHNICAL_DRAFTS[1]]
    assert "mean logits" in formulas
    assert "mean per-window sigmoid" in formulas
    assert "fallback" in formulas.lower()
    assert "not the recovered historical loader" in formulas

    figures = drafts[TECHNICAL_DRAFTS[2]]
    assert "25,770 ECG" in figures
    assert "24,666 patients" in figures
    assert "Selected Primary6 ECG | 1,643" in figures
    assert "Selected Primary8 ECG | 2,193" in figures
    assert "quarantine was not assessed" in figures

    claims = drafts[TECHNICAL_DRAFTS[3]].lower()
    assert "incident" in claims and "af statement presence" in claims
    assert "clinical validation" in claims and "withdraw" in claims
    assert "human review" in claims

    response = drafts[TECHNICAL_DRAFTS[4]]
    assert "NOT FOR SUBMISSION" in response
    assert "The manuscript has not been edited" in response
    assert ".." not in response
    assert "### R1-1" in response and "### R2-6" in response
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    for row in source["items"]:
        if row["id"].startswith("A-"):
            continue
        assert response.count(f"### {row['id']} ") == 1


def test_new_reviewer_closure_markdown_links_resolve_locally():
    documents = [PLAN_MD, *(DOCS / name for name in TECHNICAL_DRAFTS)]
    for path in documents:
        for link in re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            target = link.split("#", 1)[0]
            if target.startswith(("http://", "https://")):
                continue
            assert (path.parent / target).is_file(), f"{path.name}: {link}"


def test_action_plan_links_targeted_cedia_accounting_receipt():
    markdown = PLAN_MD.read_text(encoding="utf-8")
    receipt = DOCS / "receipts/CEDIA_TARGETED_SACCT_RECONCILIATION_2026-11-10.json"

    assert receipt.is_file()
    assert "CEDIA targeted Slurm accounting" in markdown
    assert "CEDIA_TARGETED_SACCT_RECONCILIATION_2026-11-10.json" in markdown


def test_every_editorial_only_reviewer_has_a_proposal_crosswalk():
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    editorial_ids = [
        row["id"]
        for row in source["items"]
        if row["reviewer_satisfaction"] == "EDITORIAL_ACTION_ONLY"
    ]
    proposals = (DOCS / "REVIEWER_FIGURE_TABLE_CORRECTIONS.md").read_text(
        encoding="utf-8"
    )

    assert len(editorial_ids) == 21
    for reviewer_id in editorial_ids:
        assert proposals.count(f"| {reviewer_id} |") == 1, reviewer_id


def test_proposed_tables_are_populated_from_canonical_aggregates():
    sph, canonical, p4_metrics, p4_cohort = load_inputs(ROOT)
    rendered = render_tables(sph, canonical, p4_metrics, p4_cohort)
    target = DOCS / "REVIEWER_PROPOSED_TABLES.md"

    assert target.read_text(encoding="utf-8") == rendered
    assert rendered.count("| P6:") == 10
    assert rendered.count("| P8:") == 12
    assert rendered.count("| P4:") == 6
    assert "25,770 scored ECG" in rendered
    assert "80.23% (mean binary-panel accuracy)" in rendered
    assert "95.19%" in rendered and "90.61%" in rendered
    assert "58 selected-cohort cases" in rendered
    assert "connected components of patient IDs" in rendered


def test_proposed_table_export_rejects_incomplete_or_inconsistent_aggregate():
    sph, canonical, p4_metrics, p4_cohort = load_inputs(ROOT)
    invalid = deepcopy(sph)
    invalid["endpoints"].pop("P4:IMI")

    with pytest.raises(ValueError, match="14 compatible endpoints"):
        render_tables(invalid, canonical, p4_metrics, p4_cohort)


def test_public_reviewer_artifacts_have_no_private_paths_or_row_level_keys():
    private_path = re.compile(r"(?i)(?:[A-Z]:\\Users\\|/home/diego\.)")
    row_level_key = re.compile(
        r"(?i)[\"'](?:patient|record|ecg|waveform)_(?:id|identifier|hash|sha256)[\"']\s*:"
    )

    for path in PUBLIC_REVIEWER_ARTIFACTS:
        content = path.read_text(encoding="utf-8")
        assert not private_path.search(content), path.name
        assert not row_level_key.search(content), path.name
