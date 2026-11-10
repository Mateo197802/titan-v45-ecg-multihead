from __future__ import annotations

import json
import re
import subprocess
import sys
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs/reviewer_closure"
FINAL_JSON = DOCS / "REVIEWER_15_TECHNICAL_FINAL_MATRIX.json"
FINAL_MD = DOCS / "REVIEWER_15_TECHNICAL_FINAL_MATRIX.md"
RECEIPT = DOCS / "receipts/CEDIA_JOB_LOGS_2026-11-10.json"
METRICS = DOCS / "GENERALIZATION_PER_CLASS_METRICS.json"
METRICS_SOURCE = ROOT / "outputs/results/external_sph/sph_aggregate_32669.json"
METRICS_EXPORTER = ROOT / "scripts/evaluation/export_generalization_per_class_metrics.py"

EXPECTED_IDS = {
    "R1-1", "R1-2", "R1-3", "R1-4", "R2-general", "R2-2b", "R2-3a",
    "R2-3c", "R2-3d", "R2-3e", "R2-3f", "R2-4a", "R2-4e", "R2-4k", "R2-5",
}
SUBREQUIREMENT_STATUSES = {
    "VERIFIED_COMPLETE",
    "VERIFIED_WITH_DEFINED_SCOPE",
    "EXPERIMENT_COMPLETED",
    "EXPERIMENT_COMPLETED_WITH_LIMITATIONS",
    "HISTORICAL_SOURCE_NOT_RECOVERED",
    "NEEDS_INDEPENDENT_DATA",
    "NEEDS_AUTHOR_OR_CUSTODIAN_APPROVAL",
    "NOT_SATISFIED",
}


def test_final_technical_matrix_covers_all_15_without_upgrading_source_satisfaction():
    source = json.loads((DOCS / "REVIEWER_48_DETAILED.json").read_text(encoding="utf-8"))
    final = json.loads(FINAL_JSON.read_text(encoding="utf-8"))
    source_by_id = {row["id"]: row for row in source["items"]}

    assert source["counts"] == {"total": 48, "peer_review": 36, "project_audit": 12}
    for source_row in source["items"]:
        for reference in source_row["evidence"]:
            if not reference.startswith(("http://", "https://")):
                assert (ROOT / reference).is_file(), (source_row["id"], reference)

    assert final["schema"] == "TITAN_V45_REVIEWER_15_TECHNICAL_FINAL_MATRIX_V1"
    assert {row["id"] for row in final["items"]} == EXPECTED_IDS
    assert len(final["items"]) == 15
    for row in final["items"]:
        source_row = source_by_id[row["id"]]
        assert row["reviewer_satisfaction"] == source_row["reviewer_satisfaction"]
        assert row["manuscript_state"] == "SIN_EDITAR"
        assert row["subrequirements"]
        assert all(item["status"] in SUBREQUIREMENT_STATUSES for item in row["subrequirements"])
        assert all(item["evidence_refs"] for item in row["subrequirements"])
        assert row["remaining_actions"]

    for row in final["items"]:
        for requirement in row["subrequirements"]:
            for reference in requirement["evidence_refs"]:
                if not reference.startswith(("http://", "https://")):
                    assert (ROOT / reference).is_file(), (row["id"], reference)


def test_cedia_job_receipt_is_sanitized_and_preserves_selection_gate_findings():
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    rendered = json.dumps(receipt, ensure_ascii=True)

    assert receipt["schema"] == "TITAN_V45_CEDIA_JOB_LOG_AGGREGATE_RECEIPT_V1"
    assert {job["job_id"] for job in receipt["jobs"]} == {"17296", "17314", "17315"}
    p6_sweep = next(job for job in receipt["jobs"] if job["job_id"] == "17314")
    p6_gate = next(job for job in receipt["jobs"] if job["job_id"] == "17315")
    p4 = next(job for job in receipt["jobs"] if job["job_id"] == "17296")
    assert len(p6_sweep["epochs"]) == 12
    assert p6_gate["gate"] == {"top1_accuracy_min": 0.95, "macro_f1_min": 0.8}
    assert p6_sweep["passing_epochs"] == [8]
    epoch8 = p6_sweep["epochs"][7]
    assert epoch8["external_top1_accuracy"] == 0.9519172245891662
    assert epoch8["external_macro_f1"] == 0.8009383239876123
    assert p4["calibration"]["release_config_thresholds_match"] is True
    assert p4["external_panel_evaluation"]["matches_release_headline_after_rounding_to_percent_2dp"] is True
    assert not re.search(r"[A-Za-z]:\\Users\\|/home/[^/]+", rendered)
    assert not re.search(r"(?i)(patient|record|ecg)_(id|identifier|hash|sha256)", rendered)


def test_final_matrix_markdown_links_and_identifies_scope_without_claiming_external_independence():
    text = FINAL_MD.read_text(encoding="utf-8")
    assert "P6 external-development population was used for checkpoint gating" in text
    assert "not an independent test" in text
    assert "CEDIA_JOB_LOGS_2026-11-10.json" in text
    for item_id in EXPECTED_IDS:
        assert f"### {item_id} " in text


def test_all_requested_reviewer_closure_deliverables_exist():
    required = {
        "HISTORICAL_RECOVERY_FINAL_EXECUTION.md",
        "CHECKPOINT_JOB_MANIFEST_VERIFICATION_FINAL.md",
        "SPECIALIST_192_512_ARCHITECTURE_RESOLUTION.md",
        "REPRODUCIBILITY_EXECUTION_MATRIX.json",
        "GENERALIZATION_DATASET_ELIGIBILITY.md",
        "GENERALIZATION_EXPERIMENT_PROTOCOL.md",
        "GENERALIZATION_EXPERIMENT_RESULTS.md",
        "GENERALIZATION_PER_CLASS_METRICS.json",
        "GENERALIZATION_ERROR_ANALYSIS.md",
        "OTHER_CLASS_COVERAGE_EXPERIMENT.md",
        "AUXILIARY_CLASS_TRAINING_EVIDENCE.md",
        "SELECTIVE_PREDICTION_EXPERIMENT.md",
        "REVIEWER_15_TECHNICAL_FINAL_MATRIX.md",
        "REVIEWER_15_TECHNICAL_FINAL_MATRIX.json",
    }
    assert required <= {path.name for path in DOCS.iterdir() if path.is_file()}
    assert METRICS_EXPORTER.is_file()


def test_per_class_metrics_are_deterministically_derived_from_public_aggregate(tmp_path):
    source_bytes = METRICS_SOURCE.read_bytes()
    source = json.loads(source_bytes)
    published = json.loads(METRICS.read_text(encoding="utf-8"))
    regenerated_path = tmp_path / "metrics.json"
    subprocess.run(
        [
            sys.executable,
            str(METRICS_EXPORTER),
            "--source",
            str(METRICS_SOURCE),
            "--output",
            str(regenerated_path),
            "--as-of",
            "2026-11-10",
        ],
        check=True,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    regenerated = json.loads(regenerated_path.read_text(encoding="utf-8"))

    assert published == regenerated
    assert published["source_sha256"] == sha256(source_bytes).hexdigest()
    assert published["evaluation_scope"]["independent_test"] is False
    assert published["evaluation_scope"]["clinical_adjudication"] is False
    assert len(published["endpoints"]) == 14
    assert not re.search(r"(?i)(patient|record|ecg)_(id|identifier|hash|sha256)", json.dumps(published))
    for name, row in source["endpoints"].items():
        observed = next(item for item in published["endpoints"] if item["endpoint"] == name)
        assert observed["n"] == row["metrics"]["rows"]
        assert observed["confusion"] == {
            "tp": row["metrics"]["tp"],
            "tn": row["metrics"]["tn"],
            "fp": row["metrics"]["fp"],
            "fn": row["metrics"]["fn"],
        }
