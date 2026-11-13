from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("sph_privacy", ROOT / "scripts/external_validation/audit_sph_public_json.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


@pytest.mark.parametrize("data", [{"record_id": "A12345"}, {"Patient_ID": "x"},
                                  {"nested": ["A12345"]}, {"ecg_id": "anything"}])
def test_rejects_individual_ids(data):
    with pytest.raises(ValueError):
        module.inspect_value(data)


def test_public_receipt_descriptions_and_hashes_are_allowed():
    module.inspect_value({"patient_or_record_level_data_in_repository": False,
                          "unit": "connected_component_of_patient_ids_linked_by_exact_duplicate_waveforms",
                          "sha256": "a" * 64})


def test_all_public_sph_json_files_pass():
    result = module.audit_directory(ROOT / "outputs/results/external_sph")
    assert result["json_files_checked"] >= 13
    assert result["individual_identifiers_detected"] == 0
