from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.benchmarkmax.render_sph_pac_head_comparison import render_figure

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "outputs/results/benchmarkmax/sph_pac_head_comparison_32805.json"


def test_render_pac_head_figure_from_aggregate_only(tmp_path: Path) -> None:
    pytest.importorskip("matplotlib")

    outputs = render_figure(REPORT, tmp_path)

    assert set(outputs) == {
        "sph_pac_head_comparison_32805.png",
        "sph_pac_head_comparison_32805.pdf",
        "sph_pac_head_comparison_32805.figure_manifest.json",
    }
    assert all((tmp_path / name).stat().st_size > 1000 for name in outputs)
    manifest_path = tmp_path / "sph_pac_head_comparison_32805.figure_manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    assert b"\r\n" not in manifest_bytes
    manifest = json.loads(manifest_bytes)
    assert manifest["schema"] == "TITAN_V46_SPH_PAC_HEAD_FIGURE_V1"
    assert manifest["source_aggregate_sha256"]
    assert manifest["holdout_positive_records"] == 84
    assert manifest["holdout_records"] == 3697
    assert manifest["metrics"] == ["average_precision", "sensitivity"]


def test_renderer_rejects_missing_paired_patient_interval(tmp_path: Path) -> None:
    pytest.importorskip("matplotlib")
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    del report["paired_patient_cluster_bootstrap"]["comparisons"][
        "logistic_regression_minus_frozen_v45_p8_pac"
    ]["metrics"]["average_precision"]["ci95_b"]
    invalid = tmp_path / "incomplete.json"
    invalid.write_text(json.dumps(report), encoding="utf-8")

    with pytest.raises(ValueError, match="patient-cluster interval"):
        render_figure(invalid, tmp_path / "out")


def test_renderer_rejects_nonaggregate_input(tmp_path: Path) -> None:
    invalid = tmp_path / "not-aggregate.json"
    invalid.write_text('{"schema":"individual-ledger"}', encoding="utf-8")

    with pytest.raises(ValueError, match="aggregate"):
        render_figure(invalid, tmp_path / "out")


def test_renderer_cli_runs_from_another_working_directory(tmp_path: Path) -> None:
    pytest.importorskip("matplotlib")
    output = tmp_path / "figures"
    script = ROOT / "scripts/benchmarkmax/render_sph_pac_head_comparison.py"
    result = subprocess.run(
        [
            sys.executable, str(script), "--report", str(REPORT),
            "--output-dir", str(output),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert (output / "sph_pac_head_comparison_32805.png").exists()


def test_experiment_registry_records_success_without_erasing_failed_attempts() -> None:
    registry_path = ROOT / "docs/benchmarkmax/BENCHMARKMAX_EXPERIMENT_REGISTRY.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    experiments = {item["id"]: item for item in registry["experiments"]}
    pac = experiments["B2-V46-SPH-PAC-HEAD-COMPARISON"]

    assert pac["status"] == "completed_aggregate_only_exploratory"
    assert pac["cedia_job"] == 32805
    assert pac["aggregate_sha256"] == "722c68d885bc6cef308209d2b1ac3c4f8dd7164fb8e1c26d4de527d30959989a"
    registry_root = registry_path.parent
    aggregate = registry_root / pac["aggregate_artifact"]
    assert hashlib.sha256(aggregate.read_bytes()).hexdigest() == pac["aggregate_sha256"]
    receipt = registry_root / pac["verification_receipt"]
    assert hashlib.sha256(receipt.read_bytes()).hexdigest() == pac["verification_receipt_sha256"]
    results = registry_root / pac["results_document"]
    assert hashlib.sha256(results.read_bytes()).hexdigest() == pac["results_document_sha256"]
    for path_key, hash_key in (
        ("figure_png", "figure_png_sha256"),
        ("figure_pdf", "figure_pdf_sha256"),
        ("figure_manifest", "figure_manifest_sha256"),
    ):
        artifact = registry_root / pac[path_key]
        assert hashlib.sha256(artifact.read_bytes()).hexdigest() == pac[hash_key]
    assert {attempt["cedia_job_id"] for attempt in pac["failed_attempts"]} == {
        "32799", "32800", "32802"
    }
    assert pac["external_claim_permitted"] is False

    mimic = experiments["B2-MIMIC-IV-ECG-MACHINE-REPORT-CONCORDANCE"]
    assert mimic["status"] == "metadata_audit_implemented_waiting_for_author_mapping_and_cedia_quota"
    assert mimic["mapping_author_approved"] is False
    assert mimic["downloaded"] is False
    assert mimic["metadata_downloaded"] is False
    assert mimic["performance_metrics_computed"] is False
    assert mimic["metadata_auditor_scope"] == "synthetic_contract_only_no_real_mimic_files_read"
    assert mimic["cedia_quota_check_result"].startswith("quota_command_returned_no_quota_record")
    parser = registry_root / mimic["parser"]
    template = registry_root / mimic["mapping_template"]
    metadata_auditor = registry_root / mimic["metadata_auditor"]
    metadata_module = registry_root / mimic["metadata_auditor_module"]
    metadata_tests = registry_root / mimic["metadata_auditor_tests"]
    design = registry_root / mimic["design"]
    assert hashlib.sha256(parser.read_bytes()).hexdigest() == mimic["parser_sha256"]
    assert hashlib.sha256(template.read_bytes()).hexdigest() == mimic["mapping_template_sha256"]
    assert hashlib.sha256(metadata_auditor.read_bytes()).hexdigest() == mimic["metadata_auditor_sha256"]
    assert hashlib.sha256(metadata_module.read_bytes()).hexdigest() == mimic["metadata_auditor_module_sha256"]
    assert hashlib.sha256(metadata_tests.read_bytes()).hexdigest() == mimic["metadata_auditor_tests_sha256"]
    assert hashlib.sha256(design.read_bytes()).hexdigest() == mimic["design_sha256"]


def test_pac_pilot_docs_no_longer_claim_execution_is_pending() -> None:
    readme = (ROOT / "docs/benchmarkmax/README.md").read_text(encoding="utf-8")
    feasibility = (
        ROOT / "docs/benchmarkmax/DATA_AND_LABEL_FEASIBILITY_REPORT.md"
    ).read_text(encoding="utf-8")

    assert "Job `32805` completed" in readme
    assert "completed on CEDIA job `32805`" in feasibility
    assert "No reportable aggregate or persistent candidate weights exist yet" not in readme
    assert "No candidate specialist has been trained or selected" not in feasibility
    assert "does not satisfy the external-validation requirement" in readme
    assert "source observed previously" in readme
    assert "Full waveform acquisition remains blocked" in readme
    assert "machine-report statements" in readme
