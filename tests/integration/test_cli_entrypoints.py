from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENTRYPOINTS = (
    "scripts/training/train_specialist.py",
    "scripts/training/calibrate_specialist.py",
    "scripts/training/run_optuna.py",
    "scripts/evaluation/evaluate_primary.py",
    "scripts/evaluation/evaluate_internal.py",
    "scripts/evaluation/evaluate_external_dev.py",
    "scripts/evaluation/evaluate_heads.py",
    "scripts/evaluation/evaluate_cascade.py",
    "scripts/evaluation/evaluate_uncertainty.py",
    "scripts/evaluation/generate_gradcam.py",
    "scripts/evaluation/audit_optuna.py",
    "scripts/artifacts/verify_artifact_hashes.py",
    "scripts/artifacts/audit_publication.py",
    "scripts/artifacts/fetch_release_assets.py",
    "scripts/artifacts/build_external_dev_archive.py",
    "scripts/artifacts/build_release_manifest.py",
    "scripts/artifacts/sanitize_report.py",
    "scripts/cedia/generate_cleanup_manifest.py",
)


def test_public_entrypoints_have_working_help() -> None:
    for relative in ENTRYPOINTS:
        path = ROOT / relative
        assert path.is_file(), relative
        completed = subprocess.run(
            [sys.executable, str(path), "--help"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert completed.returncode == 0, f"{relative}: {completed.stderr}"
        assert "usage:" in completed.stdout.lower()
