import csv
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
import torch

import titan_v45.data.mimic_ecg_reports as mimic_reports
from titan_v45.data.mimic_ecg_reports import (
    classify_machine_pac_report,
    iter_mimic_machine_reports,
    verify_mimic_sha256_manifest,
)

_SCORER_PATH = Path(__file__).resolve().parents[2] / (
    "scripts/external_validation/score_mimic_pac_machine_reports.py"
)
_SCORER_SPEC = importlib.util.spec_from_file_location("mimic_pac_scorer", _SCORER_PATH)
_SCORER_MODULE = importlib.util.module_from_spec(_SCORER_SPEC)
_SCORER_SPEC.loader.exec_module(_SCORER_MODULE)
_load_probe_bundle = _SCORER_MODULE._load_probe_bundle

_MIMIC_REQUIRED = (
    "LICENSE.txt", "RECORDS", "record_list.csv", "machine_measurements.csv",
    "machine_measurements_data_dictionary.csv", "waveform_note_links.csv",
)


def _write_checksum_tree(root, *, extra_files=None):
    files = {name: f"fixture:{name}\n".encode() for name in _MIMIC_REQUIRED}
    files.update(extra_files or {})
    lines = []
    for name, content in sorted(files.items()):
        path = root / Path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        lines.append(f"{hashlib.sha256(content).hexdigest()}  {name}\n")
    (root / "SHA256SUMS.txt").write_text("".join(lines), encoding="ascii")


@pytest.mark.parametrize(
    ("reports", "expected"),
    [
        (["Premature atrial complexes"], "positive_mention"),
        (["No premature atrial complexes"], "explicit_negative_mention"),
        (["PACs absent"], "explicit_negative_mention"),
        (["PACs are absent"], "explicit_negative_mention"),
        (["PACs not seen"], "explicit_negative_mention"),
        (["PACs were not observed"], "explicit_negative_mention"),
        (["PACs present; PACs are absent"], "ambiguous_mention"),
        (["Sinus rhythm, normal ECG"], "not_mentioned"),
        (["No PACs; occasional PACs"], "ambiguous_mention"),
        ([""], "missing_report_text"),
        (["Premature ventricular complexes"], "not_mentioned"),
    ],
)
def test_report_parser_uses_explicit_three_state_mentions(reports, expected):
    assert classify_machine_pac_report(reports) == expected


def test_metadata_preflight_joins_reports_without_reading_waveforms_or_exporting_ids(tmp_path):
    audit = getattr(mimic_reports, "audit_mimic_metadata_source", None)
    assert callable(audit)

    root = tmp_path / "metadata-only"
    record_list = (
        b"subject_id,study_id,file_name,ecg_time,path\n"
        b"10000001,40000001,40000001,2150-01-01 00:00:00,"
        b"files/p1000/p10000001/s40000001/40000001\n"
    )
    measurements = b"subject_id,study_id,report_0\n10000001,40000001,PACs are absent\n"
    _write_checksum_tree(
        root,
        extra_files={
            "record_list.csv": record_list,
            "machine_measurements.csv": measurements,
        },
    )
    manifest = root / "SHA256SUMS.txt"
    with manifest.open("a", encoding="ascii") as stream:
        stream.write(f"{'a' * 64}  files/p1000/p10000001/s40000001/40000001.hea\n")

    report = audit(root)

    assert report["denominators"]["paired_metadata_records"] == 1
    assert report["denominators"]["unique_subjects"] == 1
    assert report["denominators"]["report_state_counts"]["explicit_negative_mention"] == 1
    assert report["preperformance_controls"]["waveform_files_read"] is False
    assert report["preperformance_controls"]["model_performance_metrics_computed"] is False
    assert report["metadata_source_integrity"]["waveform_files_verified"] is False
    assert report["metadata_source_integrity"]["metadata_files_verified"] == len(_MIMIC_REQUIRED)
    serialized = json.dumps(report)
    assert "10000001" not in serialized
    assert "40000001" not in serialized


def test_join_uses_subject_and_study_ids_and_rejects_ambiguous_pairs(tmp_path):
    record_list = tmp_path / "record_list.csv"
    measurements = tmp_path / "machine_measurements.csv"
    with record_list.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=["subject_id", "study_id", "file_name", "ecg_time", "path"]
        )
        writer.writeheader()
        writer.writerow(
            {"subject_id": "10000001", "study_id": "40000001", "file_name": "40000001",
             "ecg_time": "2150-01-01 00:00:00",
             "path": "files/p1000/p10000001/s40000001/40000001"}
        )
    with measurements.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=["subject_id", "study_id", "report_0", "report_1"]
        )
        writer.writeheader()
        writer.writerow(
            {"subject_id": "10000001", "study_id": "40000001",
             "report_0": "Premature atrial complexes", "report_1": ""}
        )

    rows = list(iter_mimic_machine_reports(measurements, record_list))
    assert rows == [
        {
            "subject_id": "10000001",
            "study_id": "40000001",
            "record_path": "files/p1000/p10000001/s40000001/40000001",
            "report_state": "positive_mention",
        }
    ]

    with record_list.open("a", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=["subject_id", "study_id", "file_name", "ecg_time", "path"]
        )
        writer.writerow(
            {"subject_id": "10000001", "study_id": "40000001", "file_name": "40000001",
             "ecg_time": "2150-01-01 00:00:00",
             "path": "files/p1000/p10000001/s40000001/40000001"}
        )
    with pytest.raises(ValueError, match="duplicate waveform key"):
        list(iter_mimic_machine_reports(measurements, record_list))


def test_join_rejects_unmatched_machine_rows_and_missing_machine_rows(tmp_path):
    record_list = tmp_path / "record_list.csv"
    measurements = tmp_path / "machine_measurements.csv"
    with record_list.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=["subject_id", "study_id", "path"]
        )
        writer.writeheader()
        writer.writerow({"subject_id": "10000001", "study_id": "40000001",
                         "path": "files/p1000/p10000001/s40000001/40000001"})
        writer.writerow({"subject_id": "10000002", "study_id": "40000002",
                         "path": "files/p1000/p10000002/s40000002/40000002"})
    with measurements.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["subject_id", "study_id", "report_0"])
        writer.writeheader()
        writer.writerow({"subject_id": "10000003", "study_id": "40000003",
                         "report_0": "Premature atrial complexes"})

    with pytest.raises(ValueError, match="not present in record_list"):
        list(iter_mimic_machine_reports(measurements, record_list))

    with measurements.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["subject_id", "study_id", "report_0"])
        writer.writeheader()
        writer.writerow({"subject_id": "10000001", "study_id": "40000001",
                         "report_0": "Premature atrial complexes"})

    with pytest.raises(ValueError, match="missing machine-measurement rows"):
        list(iter_mimic_machine_reports(measurements, record_list))


def test_join_rejects_csv_rows_with_extra_or_missing_columns(tmp_path):
    record_list = tmp_path / "record_list.csv"
    measurements = tmp_path / "machine_measurements.csv"
    record_list.write_text(
        "subject_id,study_id,path\n10000001,40000001,files/p1000/p10000001/s40000001/40000001,extra\n",
        encoding="utf-8",
    )
    measurements.write_text(
        "subject_id,study_id,report_0\n10000001,40000001\n", encoding="utf-8"
    )

    with pytest.raises(ValueError, match="malformed MIMIC record_list row"):
        list(iter_mimic_machine_reports(measurements, record_list))

    record_list.write_text(
        "subject_id,study_id,path\n10000001,40000001,files/p1000/p10000001/s40000001/40000001\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="malformed MIMIC machine-measurement row"):
        list(iter_mimic_machine_reports(measurements, record_list))


def test_official_checksum_verifier_returns_only_aggregate_provenance(tmp_path):
    _write_checksum_tree(tmp_path, extra_files={"metadata/extra.txt": b"extra\n"})

    receipt = verify_mimic_sha256_manifest(tmp_path)

    assert receipt["verified_files"] == len(_MIMIC_REQUIRED) + 1
    assert receipt["verified_bytes"] == sum(
        (tmp_path / name).stat().st_size for name in [*_MIMIC_REQUIRED, "metadata/extra.txt"]
    )
    assert set(receipt["required_file_sha256"]) == set(_MIMIC_REQUIRED)
    assert receipt["subject_or_study_identifiers_exported"] is False
    assert receipt["waveform_records_exported"] is False


def test_official_checksum_verifier_rejects_path_traversal_and_tampering(tmp_path):
    _write_checksum_tree(tmp_path)
    outside = tmp_path.parent / "outside.txt"
    outside.write_text("outside", encoding="ascii")
    manifest = tmp_path / "SHA256SUMS.txt"
    manifest.write_text(
        f"{hashlib.sha256(b'outside').hexdigest()}  ../outside.txt\n", encoding="ascii"
    )
    with pytest.raises(ValueError, match="unsafe or duplicate path"):
        verify_mimic_sha256_manifest(tmp_path)

    _write_checksum_tree(tmp_path)
    (tmp_path / "record_list.csv").write_text("tampered", encoding="ascii")
    with pytest.raises(ValueError, match="hash mismatch"):
        verify_mimic_sha256_manifest(tmp_path)


def test_official_checksum_verifier_rejects_symlinked_manifest_parent(tmp_path, monkeypatch):
    _write_checksum_tree(tmp_path)
    linked = tmp_path / "linked"
    linked.mkdir()
    (linked / "extra.txt").write_text("extra", encoding="ascii")
    manifest = tmp_path / "SHA256SUMS.txt"
    with manifest.open("a", encoding="ascii") as stream:
        stream.write(f"{hashlib.sha256(b'extra').hexdigest()}  linked/extra.txt\n")
    original_is_symlink = Path.is_symlink

    def simulated_symlink(path):
        return path == linked or original_is_symlink(path)

    monkeypatch.setattr(Path, "is_symlink", simulated_symlink)

    with pytest.raises(ValueError, match="symlink"):
        verify_mimic_sha256_manifest(tmp_path)


def test_mimic_scorer_rejects_nonfinite_or_nonpositive_probe_scaling(tmp_path):
    bundle_path = tmp_path / "pac_probe.pt"
    bundle = {
        "schema": "TITAN_V45_PAC_PROBE_MODEL_BUNDLE_PRIVATE_V1",
        "protocol_commit": "a" * 40,
        "protocol_config_sha256": "b" * 64,
        "v3f_checkpoint_sha256": "c" * 64,
        "logistic": {
            "mean": torch.zeros(1280),
            "scale": torch.ones(1280),
            "coefficient": torch.zeros(1280),
            "intercept": 0.0,
        },
        "mlp": {
            "input_dim": 1280,
            "seed": 1,
            "epochs": 1,
            "batch_size": 2,
            "learning_rate": 0.001,
            "weight_decay": 0.0001,
            "dropout": 0.2,
            "mean": torch.zeros(1280),
            "scale": torch.ones(1280),
            "state_dict": {},
        },
    }
    bundle["logistic"]["scale"][0] = 0.0
    torch.save(bundle, bundle_path)
    bundle_hash = hashlib.sha256(bundle_path.read_bytes()).hexdigest()

    with pytest.raises(ValueError, match="nonfinite or nonpositive"):
        _load_probe_bundle(
            bundle_path, bundle_hash, commit="a" * 40,
            config_hash="b" * 64, model_sha256="c" * 64,
        )

