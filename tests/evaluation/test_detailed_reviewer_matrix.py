from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "reviewer_index", ROOT / "scripts/evaluation/export_reviewer_index.py"
)
REVIEWER_INDEX = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REVIEWER_INDEX)
RENDERER_SPEC = importlib.util.spec_from_file_location(
    "reviewer_detail_renderer", ROOT / "scripts/evaluation/render_reviewer_details.py"
)
RENDERER = importlib.util.module_from_spec(RENDERER_SPEC)
RENDERER_SPEC.loader.exec_module(RENDERER)

TECHNICAL_STATUSES = {
    "VERIFIED_COMPLETE",
    "EXPERIMENT_COMPLETED_WITH_LIMITATIONS",
    "VERIFIED_WITH_LIMITATIONS",
    "EVIDENCE_CEILING_REACHED",
    "ACTIVE_RECOVERY_REQUIRED",
    "NEW_EXPERIMENT_REQUIRED",
    "MANUSCRIPT_ONLY_PENDING",
}
SATISFACTION_STATUSES = {
    "FULLY_ADDRESSED_BY_EVIDENCE",
    "PARTIALLY_ADDRESSED",
    "ADDRESSED_BY_SCOPE_RESTRICTION",
    "NOT_SATISFIED",
    "EDITORIAL_ACTION_ONLY",
    "NOT_APPLICABLE_AUDIT",
}
REQUIRED_FIELDS = {
    "id",
    "origin",
    "request",
    "manuscript_scope",
    "technical_status",
    "reviewer_satisfaction",
    "evidence",
    "protocol_population_result",
    "addressed_scope",
    "unresolved",
    "recovery_assessment",
    "experiment_requirement",
    "editorial_action",
    "scientific_risk",
}


def test_detailed_matrix_covers_48_items_and_keeps_two_status_dimensions():
    data = json.loads(
        (ROOT / "docs/reviewer_closure/REVIEWER_48_DETAILED.json").read_text(
            encoding="utf-8"
        )
    )
    items = data["items"]
    ids = [item["id"] for item in items]
    assert len(ids) == 48
    assert len(set(ids)) == 48
    assert set(ids) == REVIEWER_INDEX.expected_ids()
    assert data["counts"] == {
        "total": 48,
        "peer_review": 36,
        "project_audit": 12,
    }

    for item in items:
        assert REQUIRED_FIELDS <= item.keys(), item["id"]
        assert item["technical_status"] in TECHNICAL_STATUSES, item["id"]
        assert item["reviewer_satisfaction"] in SATISFACTION_STATUSES, item["id"]
        assert item["request"] and item["manuscript_scope"]
        assert item["protocol_population_result"] and item["unresolved"]
        assert item["editorial_action"] and item["scientific_risk"]
        assert isinstance(item["evidence"], list)
        for evidence in item["evidence"]:
            if evidence.startswith("http"):
                continue
            assert (ROOT / evidence).is_file(), f"{item['id']}: {evidence}"
        if item["id"].startswith("A-"):
            assert item["reviewer_satisfaction"] == "NOT_APPLICABLE_AUDIT"
        else:
            assert item["reviewer_satisfaction"] != "NOT_APPLICABLE_AUDIT"


def test_optuna_a10_disposition_is_linked_to_separate_pr_not_embedded_in_pr3():
    data = json.loads(
        (ROOT / "docs/reviewer_closure/REVIEWER_48_DETAILED.json").read_text(
            encoding="utf-8"
        )
    )
    item = next(row for row in data["items"] if row["id"] == "A-06")

    assert "https://github.com/Mateo197802/titan-v45-ecg-multihead/pull/4" in item[
        "evidence"
    ]
    assert all("OPTUNA_A10_RESCUE_AND_RIGHTS.md" not in ref for ref in item["evidence"])


def test_figure_1_and_2_archive_evidence_keeps_authorship_and_execution_limits():
    data = json.loads(
        (ROOT / "docs/reviewer_closure/REVIEWER_48_DETAILED.json").read_text(
            encoding="utf-8"
        )
    )
    item = next(row for row in data["items"] if row["id"] == "R2-2b")
    evidence = (ROOT / "docs/reviewer_closure/R2-2B_FIGURES_1_2_PROVENANCE.md").read_text(
        encoding="utf-8"
    )

    assert item["technical_status"] == "ACTIVE_RECOVERY_REQUIRED"
    assert item["reviewer_satisfaction"] == "PARTIALLY_ADDRESSED"
    assert "36c1c6db30a759ef9d349ae2e545577cfd7ce3af91a3b97fb459380113f294a8" in evidence
    assert "does **not** establish who created or edited them" in evidence
    assert "do not independently establish that every depicted operation was executed" in evidence


def test_detailed_markdown_exposes_each_case_and_status_pair():
    data = json.loads(
        (ROOT / "docs/reviewer_closure/REVIEWER_48_DETAILED.json").read_text(
            encoding="utf-8"
        )
    )
    markdown = (ROOT / "docs/reviewer_closure/REVIEWER_48_DETAILED.md").read_text(
        encoding="utf-8"
    )
    for item in data["items"]:
        heading = f"### {item['id']}"
        assert heading in markdown
        assert item["technical_status"] in markdown
        assert item["reviewer_satisfaction"] in markdown
    assert RENDERER.render(data) == markdown
    assert all(line == line.rstrip(" \t") for line in markdown.splitlines())


@pytest.mark.parametrize("filename", ["REVIEWER_48_DETAILED.md", "REVIEWER_48_DETAILED.json"])
def test_detailed_matrix_artifacts_are_present(filename):
    assert (ROOT / "docs/reviewer_closure" / filename).is_file()


def test_closure_documents_have_no_broken_local_links():
    documents = (
        "docs/reviewer_closure/REVIEWER_48_DETAILED.md",
        "docs/reviewer_closure/FINAL_TECHNICAL_EVIDENCE_CLOSURE.md",
        "docs/reviewer_closure/EVIDENCE_TO_CLAIM_MAP.md",
        "docs/reviewer_closure/MANUSCRIPT_READINESS_CHECKLIST.md",
        "docs/reviewer_closure/ALL_INPUT_FLOW_COVERAGE.md",
        "docs/reviewer_closure/AF_PVC_REFERENCE_DISPOSITION.md",
        "docs/reviewer_closure/REVIEWER_48_STATUS.md",
        "docs/reviewer_closure/R2-2B_FIGURES_1_2_PROVENANCE.md",
        "docs/reviewer_closure/EVIDENCE_COMMITS.md",
        "docs/reviewer_closure/EVIDENCE_SOURCE_TRIAGE.md",
        "docs/reviewer_closure/RECOVERED_VS_MISSING_HISTORICAL_EVIDENCE.md",
        "docs/reviewer_closure/CHECKPOINT_TO_PATIENT_SPLIT_LINEAGE.md",
        "docs/reviewer_closure/HISTORICAL_LOADER_IDENTITY_AND_REPLAY.md",
        "docs/reviewer_closure/OTHER_AUX_ROUTING_AND_QUARANTINE_PROVENANCE.md",
        "docs/reviewer_closure/CUSTODIAN_BACKUP_REQUEST.md",
        "docs/reviewer_closure/SPLIT_CALIBRATION_DISPOSITION.md",
    )
    for relative_path in documents:
        path = ROOT / relative_path
        links = re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8"))
        for link in links:
            target = link.split("#", 1)[0]
            if target.startswith(("http://", "https://")):
                continue
            assert (path.parent / target).is_file(), f"{relative_path}: {link}"
