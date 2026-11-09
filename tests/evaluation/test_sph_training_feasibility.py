from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "sph_training_feasibility",
    ROOT / "scripts/benchmarkmax/audit_sph_training_feasibility.py",
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_patient_split_is_stable_and_label_blind():
    patients = [f"patient-{index}" for index in range(100)]
    first = {patient: module.assign_split(patient) for patient in patients}
    second = {patient: module.assign_split(patient) for patient in reversed(patients)}
    assert first == second
    assert set(first.values()) == {"train", "development", "calibration"}
    assert module.assign_split("same-patient") == module.assign_split("same-patient")


def test_report_aggregates_by_patient_and_never_exports_identifiers():
    dictionary = {
        165: "Anteroseptal MI",
        161: "Inferior MI",
        142: "Left ventricular hypertrophy",
        30: "Atrial premature complex(es)",
        60: "Ventricular premature complex(es)",
        106: "Right bundle-branch block",
    }
    rows = [
        {"ECG_ID": "ecg-a", "Patient_ID": "patient-shared", "AHA_Code": "165;142+X"},
        {"ECG_ID": "ecg-b", "Patient_ID": "patient-shared", "AHA_Code": "142"},
        {"ECG_ID": "ecg-c", "Patient_ID": "patient-other", "AHA_Code": "30"},
    ]
    report = module.build_report(rows, "a" * 64, "b" * 64, "c" * 64, dictionary)
    serialized = json.dumps(report)
    assert "ecg-a" not in serialized
    assert "patient-shared" not in serialized
    assert report["individual_identifiers_exported"] is False
    assert report["split"]["patient_overlap_across_splits"] == 0
    total_records = sum(value["records"] for value in report["splits"].values())
    total_patients = sum(value["patients"] for value in report["splits"].values())
    assert total_records == 3
    assert total_patients == 2
    for split, value in report["splits"].items():
        assert value["endpoints"]["LVH"]["positive_records"] == (
            2 if split == module.assign_split("patient-shared") else 0
        )
        assert value["endpoints"]["LVH"]["positive_patients"] == (
            1 if split == module.assign_split("patient-shared") else 0
        )


def test_report_rejects_duplicate_or_missing_identifiers():
    dictionary = {
        165: "Anteroseptal MI",
        161: "Inferior MI",
        142: "Left ventricular hypertrophy",
        30: "Atrial premature complex(es)",
        60: "Ventricular premature complex(es)",
        106: "Right bundle-branch block",
    }
    row = {"ECG_ID": "ecg-a", "Patient_ID": "patient-a", "AHA_Code": "165"}
    with pytest.raises(ValueError, match="duplicate ECG"):
        module.build_report([row, row], "a" * 64, "b" * 64, "c" * 64, dictionary)
    with pytest.raises(ValueError, match="missing patient"):
        module.build_report(
            [{"ECG_ID": "ecg-b", "Patient_ID": "", "AHA_Code": "165"}],
            "a" * 64,
            "b" * 64,
            "c" * 64,
            dictionary,
        )


def test_report_rejects_invalid_codes():
    dictionary = {
        165: "Anteroseptal MI",
        161: "Inferior MI",
        142: "Left ventricular hypertrophy",
        30: "Atrial premature complex(es)",
        60: "Ventricular premature complex(es)",
        106: "Right bundle-branch block",
    }
    with pytest.raises(ValueError, match="invalid code"):
        module.build_report(
            [{"ECG_ID": "ecg-a", "Patient_ID": "patient-a", "AHA_Code": "not-code"}],
            "a" * 64,
            "b" * 64,
            "c" * 64,
            dictionary,
        )


def test_target_codes_must_match_the_source_dictionary():
    dictionary = {code: f"label-{code}" for code in module.TARGETS.values()}
    with pytest.raises(ValueError, match="does not match frozen endpoint"):
        module.validate_target_dictionary(dictionary)


def test_private_paths_cannot_be_written_inside_a_checkout(tmp_path):
    repository = tmp_path / "repository"
    private = repository / "outputs" / "private.json"
    with pytest.raises(ValueError, match="outside all Git checkouts"):
        module._assert_outside(private, [repository], "private output")
    module._assert_outside(tmp_path / "private.json", [repository], "private output")
