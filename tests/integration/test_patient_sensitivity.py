from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/evaluation/bootstrap_primary4_patients.py"
SPEC = importlib.util.spec_from_file_location("patient_sensitivity_cli", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def _fixture(root: Path) -> Path:
    evidence = root / "outputs/results/external_dev/evidence"
    evidence.mkdir(parents=True)
    for label in ("ASMI", "LVH", "IMI", "ISC_"):
        path = evidence / f"pathology_primary4_{label}_record_predictions.csv"
        with path.open("w", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["record_id", "source", "target", "predicted"])
            writer.writerow(["ptbxl_1", "source", 1, 1])
            writer.writerow(["ptbxl_2", "source", 1, 0])
    metadata = root / "metadata.csv"
    metadata.write_text("ecg_id,patient_id,strat_fold\n1,PRIVATE_ID,10\n2,PRIVATE_ID,10\n")
    return metadata


def test_sensitivity_maps_source_patients_without_exporting_identifiers(tmp_path: Path) -> None:
    metadata = _fixture(tmp_path)
    report = module.patient_sensitivity(tmp_path, metadata, n_bootstrap=100, seed=12)
    assert report["panel_rows"] == 8
    assert report["unique_ecgs"] == 2
    assert report["unique_patients"] == 1
    assert report["fold_counts"] == {"10": 2}
    assert report["bootstrap"]["mean_panel_accuracy"]["low"] == 0.5
    assert report["bootstrap"]["macro_f1"]["high"] == pytest.approx(2 / 3)
    assert "PRIVATE_ID" not in json.dumps(report)


def test_sensitivity_refuses_partial_patient_mapping(tmp_path: Path) -> None:
    metadata = _fixture(tmp_path)
    metadata.write_text("ecg_id,patient_id,strat_fold\n1,P1,10\n")
    with pytest.raises(ValueError, match="all evaluated ECGs"):
        module.patient_sensitivity(tmp_path, metadata, n_bootstrap=10, seed=12)
