import csv
import hashlib
import io
import json
import tarfile
from pathlib import Path

import h5py
import numpy as np
import pytest

from titan_v45.data.sph import (
    open_sph_records,
    parse_aha,
    read_sph_metadata,
    read_sph_signal,
    read_sph_signal_index,
)
from titan_v45.data.sph_duplicates import audit_sph_duplicates


def test_primary_and_modifiers_do_not_become_interchangeable():
    assert parse_aha("50+346;161+332", {50, 161}, {346, 332}) == (
        (50, (346,)), (161, (332,)),
    )
    with pytest.raises(ValueError):
        parse_aha("346+50", {50}, {346})
    assert parse_aha("50;50+346", {50}, {346}) == ((50, ()), (50, (346,)))
    with pytest.raises(ValueError):
        parse_aha("50+346+346", {50}, {346})


def test_metadata_is_record_unique_but_patient_can_repeat():
    header = "ECG_ID,AHA_Code,Patient_ID,Age,Sex,N,Date\n"
    one = "A00001,50,P1,21,F,5000,2019-01-01\n"
    two = "A00002,50,P1,21,F,5500,2019-01-01\n"
    valid = read_sph_metadata(header + one + two, {50}, set())
    assert len(valid) == 2 and valid["A00001"].patient == valid["A00002"].patient
    with pytest.raises(ValueError, match="duplicate"):
        read_sph_metadata(header + one + one, {50}, set())


def test_signal_index_reads_only_record_key_and_sample_count():
    assert read_sph_signal_index("ECG_ID,N\nA00001,5000\n") == {"A00001": 5000}
    with pytest.raises(ValueError, match="duplicate"):
        read_sph_signal_index("ECG_ID,N\nA00001,5000\nA00001,5000\n")
    with pytest.raises(ValueError, match="invalid"):
        read_sph_signal_index("ECG_ID,N\nnot-an-id,5000\n")


def test_tar_format_is_probed_and_paths_are_not_extracted(tmp_path):
    data = io.BytesIO()
    with h5py.File(data, "w") as handle:
        handle["ecg"] = np.zeros((12, 5000), dtype=np.int16)
    raw = data.getvalue()
    archive = tmp_path / "records.tar.gz"
    with tarfile.open(archive, "w") as handle:
        member = tarfile.TarInfo("records/A00001.h5")
        member.size = len(raw)
        handle.addfile(member, io.BytesIO(raw))
    [(name, content)] = list(open_sph_records(archive))
    assert name == "A00001"
    assert read_sph_signal(content, 5000)[0].shape == (12, 5000)
    with pytest.raises(ValueError, match="shape"):
        read_sph_signal(content, 5001)
    with tarfile.open(archive, "w") as handle:
        member = tarfile.TarInfo("../A00001.h5")
        member.size = len(raw)
        handle.addfile(member, io.BytesIO(raw))
    with pytest.raises(ValueError, match="path"):
        list(open_sph_records(archive))


def test_exact_duplicate_audit_reports_cross_patient_label_conflict_privately(tmp_path):
    rows = [
        ("A00001", "50", "P1", "2019-01-01"),
        ("A00002", "161", "P2", "2019-01-02"),
        ("A00003", "50", "P1", "2019-01-03"),
    ]
    with (tmp_path / "code.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Category", "Code", "Description"])
        writer.writerow(["Primary", 50, "AFIB"])
        writer.writerow(["Primary", 161, "IMI"])
        writer.writerow(["Modifier", 346, "test"])
    with (tmp_path / "metadata.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["ECG_ID", "AHA_Code", "Patient_ID", "Age", "Sex", "N", "Date"])
        for record, code, patient, date in rows:
            writer.writerow([record, code, patient, 21, "F", 5000, date])
    data = io.BytesIO()
    values = np.arange(12 * 5000, dtype=np.int16).reshape(12, 5000)
    with h5py.File(data, "w") as h5:
        h5["ecg"] = values
    duplicate_data = data.getvalue()
    data2 = io.BytesIO()
    with h5py.File(data2, "w") as h5:
        h5["ecg"] = values + 1
    archive_path = tmp_path / "records.tar.gz"
    with tarfile.open(archive_path, "w") as archive:
        for record, _, _, _ in rows:
            raw = data2.getvalue() if record == "A00003" else duplicate_data
            member = tarfile.TarInfo(f"records/{record}.h5")
            member.size = len(raw)
            archive.addfile(member, io.BytesIO(raw))
    private = tmp_path.parent / f"{tmp_path.name}-private.jsonl"
    report = audit_sph_duplicates(tmp_path, private)
    assert report["records_hashed"] == 3
    assert report["exact_duplicate_groups"] == 1
    assert report["exact_duplicate_excess_records"] == 1
    assert report["groups_crossing_patient_ids"] == 1
    assert report["groups_with_primary_code_set_conflicts"] == 1
    assert report["patient_components_linked_by_exact_duplicates"]["count"] == 1
    assert not report["record_or_patient_identifiers_exported"]
    assert len(private.read_text().splitlines()) == 3


def test_native_inventory_receipt_is_not_a_performance_claim():
    result = Path(__file__).resolve().parents[2] / (
        "outputs/results/external_sph/source_inventory_32617.json"
    )
    raw = result.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == (
        "8321abf1d91f0a97ae65b8e9d3a47ba4f5460055ac7780fd84ad2cc86efd2cf7"
    )
    audit = json.loads(raw)
    assert audit["metadata_ecgs"] == audit["archive_ecgs"] == audit["valid_signal_ecgs"] == 25770
    assert audit["metadata_patients"] == 24666
    assert audit["exact_duplicate_signal_groups"] == 168
    assert audit["technical_failures"] == {}
    assert not audit["record_or_patient_identifiers_exported"]
    assert not audit["model_inference_performed"]
