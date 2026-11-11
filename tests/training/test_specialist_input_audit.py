import csv
import hashlib
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "specialist_audit_inputs", ROOT / "scripts/specialist_experiments/audit_inputs.py"
)
audit_inputs = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit_inputs)


def _write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def test_exact_duplicate_prefers_training_and_is_scoped_to_task():
    rows = [
        {"task": "rhythm", "source": "georgia", "split": "source_holdout",
         "signal_sha256": "same", "identity_hash": "a", "excluded_reason": None},
        {"task": "rhythm", "source": "cpsc2018", "split": "train",
         "signal_sha256": "same", "identity_hash": "b", "excluded_reason": None},
        {"task": "pathology", "source": "ptbxl", "split": "train",
         "signal_sha256": "same", "identity_hash": "c", "excluded_reason": None},
    ]

    audit_inputs._deduplicate(rows)

    assert rows[0]["excluded_reason"] == "byte_identical_waveform_sha256_duplicate"
    assert rows[1]["excluded_reason"] is None
    assert rows[2]["excluded_reason"] is None


def test_challenge_inventory_excludes_previously_public_georgia_record(tmp_path):
    repo = tmp_path / "repo"
    manifest = repo / "data/manifests/external_dev/rhythm_primary8_records.csv"
    _write(manifest, b"source,record_id\ntraining/georgia,georgia_001.hea\n")
    raw = tmp_path / "cache/00_FUENTES_FISICAS_RAW"
    for source in audit_inputs.RHYTHM_ROOTS:
        (raw / source).mkdir(parents=True)
    records = {
        "chapman_shaoxing": ("c1", "164889003,59118001"),
        "cpsc2018": ("p1", "164889003,270492004"),
        "georgia": ("georgia_001", "164889003,427084000"),
    }
    for source, (name, dx) in records.items():
        _write(raw / source / f"{name}.hea", f"{name} 12 500 5000\n#Dx: {dx}\n".encode())
        _write(raw / source / f"{name}.mat", f"waveform-{source}".encode())
    config = {"study_id": "test", "rhythm": {"chapman_split": {"seed": 1}}}

    rows = audit_inputs._challenge_records(tmp_path / "cache", config, repo)

    georgia = next(row for row in rows if row["source"] == "georgia")
    assert georgia["split"] == "source_holdout"
    assert georgia["excluded_reason"] == "previous_public_v45_evaluation_record"
    assert georgia["mask"] == [1, 1, 1, 0, 1, 1, 1, 1]


def test_ptbxl_audit_never_opens_fold10_and_uses_patient_grouped_fold9(tmp_path, monkeypatch):
    root = tmp_path / "cache/00_FUENTES_FISICAS_RAW/ptb-xl"
    database = root / "ptbxl_database.csv"
    statements = root / "scp_statements.csv"
    fields = ["patient_id", "ecg_id", "strat_fold", "filename_lr", "scp_codes"]
    rows = [
        {"patient_id": str(fold), "ecg_id": str(fold), "strat_fold": str(fold),
         "filename_lr": f"records/{fold:02d}/record", "scp_codes": "{'ASMI': 100}"}
        for fold in range(1, 10)
    ]
    rows.append({"patient_id": "999", "ecg_id": "999", "strat_fold": "10",
                 "filename_lr": "../../must-not-be-read", "scp_codes": "not a literal"})
    database.parent.mkdir(parents=True)
    with database.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    statements.write_text("statement fixture\n", encoding="utf-8")
    for fold in range(1, 10):
        base = root / f"records/{fold:02d}/record"
        _write(base.with_suffix(".hea"), b"record 12 100 1000\n")
        _write(base.with_suffix(".dat"), f"wave-{fold}".encode())
    monkeypatch.setattr(audit_inputs, "PTBXL_DATABASE_SHA256", hashlib.sha256(database.read_bytes()).hexdigest())
    monkeypatch.setattr(audit_inputs, "PTBXL_SCP_SHA256", hashlib.sha256(statements.read_bytes()).hexdigest())
    config = {"study_id": "test", "pathology": {"split": {"seed": 20261111}}}

    records, receipt = audit_inputs._ptbxl_records(tmp_path / "cache", config)

    assert len(records) == 9
    assert receipt["fold10_accessed"] is False
    assert {row["fold"] for row in records} == set(range(1, 10))
    assert {row["split"] for row in records if row["fold"] == 9} <= {
        "calibration", "internal_evaluation"
    }
    assert all(row["mask"] == [1, 0, 0, 0] for row in records)


def test_waveform_qc_is_descriptive_and_reports_nonfinite_and_flat_leads(tmp_path):
    source_root = tmp_path / "00_FUENTES_FISICAS_RAW/chapman_shaoxing"
    _write(source_root / "r1.hea", b"header")
    _write(source_root / "r1.mat", b"wave")
    rows = [
        {"source": "chapman_shaoxing", "relative_record": "r1",
         "excluded_reason": None},
        {"source": "chapman_shaoxing", "relative_record": "excluded",
         "excluded_reason": "duplicate"},
    ]

    class FakeWFDB:
        @staticmethod
        def rdheader(_):
            return SimpleNamespace(sig_len=20, fs=2)

        @staticmethod
        def rdrecord(_, *, sampfrom, sampto):
            assert (sampfrom, sampto) == (0, 20)
            return SimpleNamespace(
                p_signal=np.asarray([[0.0, 0.0], [1.0, np.nan]]),
                units=["mV", "mV"],
            )

    result = audit_inputs._waveform_qc(tmp_path, rows, wfdb_module=FakeWFDB)
    source_qc = result["chapman_shaoxing"]

    assert source_qc["records_attempted"] == 1
    assert source_qc["records_with_nonfinite_values"] == 1
    assert source_qc["records_all_zero"] == 0
    assert source_qc["flat_leads_total"] == 1
    assert source_qc["units_by_record"] == {"mV": 1}
    assert source_qc["max_abs_physical_value_by_unit"]["mV"]["maximum_record_peak"] == 1.0
    assert source_qc["exclusion_policy"] == "descriptive_only_no_records_removed_by_this_qc"
