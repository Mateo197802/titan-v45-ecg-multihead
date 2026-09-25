from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from titan_v45.evaluation.release_evidence import _sha256_lf_normalized

ROOT = Path(__file__).resolve().parents[2]
VERIFIER = ROOT / "scripts" / "evaluation" / "verify_release_evidence.py"


def _run_verifier(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VERIFIER), "--root", str(root)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_evidence_hashes_are_stable_across_text_line_endings(tmp_path: Path) -> None:
    lf = tmp_path / "lf.json"
    crlf = tmp_path / "crlf.json"
    lf.write_bytes(b'{"metric": 1}\n')
    crlf.write_bytes(b'{"metric": 1}\r\n')

    assert _sha256_lf_normalized(lf) == _sha256_lf_normalized(crlf)


def test_verifier_recomputes_canonical_metrics_from_record_evidence() -> None:
    result = _run_verifier(ROOT)

    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["verification"] == "passed"
    snapshot = json.loads(
        (ROOT / "outputs/results/release_evidence_verification.json").read_text(encoding="utf-8")
    )
    assert report == snapshot
    assert report["profiles"]["rhythm_primary6_diagnostic"]["records"] == 1643
    assert report["profiles"]["rhythm_primary6_diagnostic"]["accuracy"] == 0.9519172245891662
    assert report["profiles"]["rhythm_primary6_diagnostic"]["macro_f1"] == pytest.approx(
        0.8009383239876123, abs=1e-12
    )
    assert report["profiles"]["rhythm_primary8"]["accepted_accuracy"] == pytest.approx(
        0.9060647514819882, abs=1e-12
    )
    assert report["profiles"]["rhythm_primary8"]["macro_f1"] == pytest.approx(
        0.7614253535094375, abs=1e-12
    )
    assert report["profiles"]["rhythm_primary8"]["single_label_accuracy"] == pytest.approx(
        1870 / 2193, abs=1e-12
    )
    assert report["profiles"]["pathology_primary4"]["panel_rows"] == 962
    assert report["profiles"]["pathology_primary4"]["mean_accuracy"] == pytest.approx(
        0.8022904853689048, abs=1e-12
    )
    assert report["profiles"]["pathology_primary4"]["macro_f1"] == pytest.approx(
        0.793456370406346, abs=1e-12
    )
    assert "outputs/results/external_dev/evidence/rhythm_primary8_record_predictions.csv" in report[
        "input_sha256_lf_normalized"
    ]
    assert "src/titan_v45/evaluation/release_evidence.py" in report["input_sha256_lf_normalized"]


def test_verifier_rejects_canonical_metrics_that_disagree_with_predictions(
    tmp_path: Path,
) -> None:
    source_files = [
        "release-manifest.json",
        "outputs/results/primary/canonical_profiles.json",
        "outputs/results/external_dev/rhythm_primary8_metrics.json",
        "outputs/results/external_dev/rhythm_primary6_metrics.json",
        "outputs/results/external_dev/pathology_primary4_metrics.json",
        "outputs/results/external_dev/evidence/rhythm_primary8_record_predictions.csv",
        "outputs/results/external_dev/evidence/rhythm_primary6_record_predictions.csv",
        "outputs/results/external_dev/evidence/pathology_primary4_ASMI_record_predictions.csv",
        "outputs/results/external_dev/evidence/pathology_primary4_LVH_record_predictions.csv",
        "outputs/results/external_dev/evidence/pathology_primary4_IMI_record_predictions.csv",
        "outputs/results/external_dev/evidence/pathology_primary4_ISC__record_predictions.csv",
        "data/manifests/external_dev/rhythm_primary8_records.csv",
        "data/manifests/external_dev/rhythm_primary6_diagnostic_records.csv",
        "data/manifests/external_dev/pathology_primary4_panels.csv",
        "data/external_dev/rhythm/release_cohort_report.json",
        "data/external_dev/pathology/release_cohort_report.json",
        "scripts/evaluation/verify_release_evidence.py",
        "src/titan_v45/evaluation/release_evidence.py",
    ]
    for relative in source_files:
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)

    metrics_path = tmp_path / "outputs/results/external_dev/rhythm_primary6_metrics.json"
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    metrics["top1_accuracy"] = 0.80
    metrics_path.write_text(json.dumps(metrics), encoding="utf-8")

    result = _run_verifier(tmp_path)

    assert result.returncode == 1
    assert "Primary6 top-1 accuracy:" in result.stderr
