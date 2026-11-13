import csv
import hashlib
import importlib.util
import json
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


class FakeHeaderWFDB:
    @staticmethod
    def rdheader(_):
        return SimpleNamespace(n_sig=12, fs=500, sig_len=1000)


def _write_eval_manifests(repo, primary8_rows, primary6_rows):
    manifest_dir = repo / "data/manifests/external_dev"
    manifest_dir.mkdir(parents=True)
    items = []
    for name, rows in (
        ("rhythm_primary8_records.csv", primary8_rows),
        ("rhythm_primary6_diagnostic_records.csv", primary6_rows),
    ):
        content = "source,record_id,record_base\n" + "".join(
            f"{source},{record_id},records/{record_id}/{record_id}\n"
            for source, record_id in rows
        )
        path = _write(manifest_dir / name, content.encode())
        items.append({
            "path": path.relative_to(repo).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        })
    return {"data_policy": {"prior_v45_public_rhythm_evaluation_records": {"manifests": items}}}


def test_header_summary_uses_wfdb_for_physical_header_fields(tmp_path):
    header = _write(
        tmp_path / "chapman.hea",
        b"chapman 12 500 500000/mV 16 0 15 31255\n",
    )
    calls = []

    class Parser:
        @staticmethod
        def rdheader(record_name):
            calls.append(record_name)
            return SimpleNamespace(n_sig=12, fs=500, sig_len=31255)

    summary = audit_inputs._header_summary(header, Parser)

    assert calls == [str(header.with_suffix(""))]
    assert summary == {
        "lead_count": 12,
        "sample_rate_hz": 500.0,
        "duration_seconds": 62.51,
    }


def test_parallel_audit_helper_preserves_order_and_logs_only_progress_counts(capsys):
    result = audit_inputs._parallel_map("fixture stage", lambda value: value * 2, [1, 2, 3])

    assert result == [2, 4, 6]
    assert capsys.readouterr().out.endswith("[preflight] fixture stage: 3/3\n")


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


def test_exact_duplicate_of_prior_public_evaluation_is_never_reintroduced():
    rows = [
        {"task": "rhythm", "source": "chapman_shaoxing", "split": "train",
         "signal_sha256": "known-eval-wave", "identity_hash": "a",
         "excluded_reason": "previous_public_v45_evaluation_record"},
        {"task": "rhythm", "source": "cpsc2018", "split": "train",
         "signal_sha256": "known-eval-wave", "identity_hash": "b", "excluded_reason": None},
    ]

    audit_inputs._deduplicate(rows)

    assert rows[1]["excluded_reason"] == "byte_identical_previous_public_v45_evaluation_waveform"


def test_challenge_inventory_excludes_previously_public_georgia_record(tmp_path):
    repo = tmp_path / "repo"
    config = _write_eval_manifests(repo, [("training/georgia", "georgia_001")], [])
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
    config.update({"study_id": "test", "rhythm": {"chapman_split": {"seed": 1}}})

    rows, manifest_audit = audit_inputs._challenge_records(
        tmp_path / "cache", config, repo, wfdb_module=FakeHeaderWFDB
    )

    georgia = next(row for row in rows if row["source"] == "georgia")
    assert georgia["split"] == "source_holdout"
    assert georgia["excluded_reason"] == "previous_public_v45_evaluation_record"
    assert georgia["mask"] == [1, 1, 1, 0, 1, 1, 1, 1]
    assert manifest_audit["union_unique_records_by_source"] == {"georgia": 1}
    assert "georgia_001" not in str(manifest_audit)


def test_public_p6_p8_records_are_excluded_in_every_rhythm_source(tmp_path):
    repo = tmp_path / "repo"
    config = _write_eval_manifests(
        repo,
        [("chapman_shaoxing", "c1"), ("training/cpsc_2018", "p1")],
        [("chapman_shaoxing", "c2"), ("training/cpsc_2018_extra", "p2")],
    )
    config.update({"study_id": "test", "rhythm": {"chapman_split": {"seed": 1}}})
    raw = tmp_path / "cache/00_FUENTES_FISICAS_RAW"
    for source in audit_inputs.RHYTHM_ROOTS:
        (raw / source).mkdir(parents=True)
    records = {
        "chapman_shaoxing": [("c1", "164889003"), ("c2", "59118001"), ("c3", "426177001")],
        "cpsc2018": [("p1", "270492004"), ("p2", "164889003"), ("p3", "427172004")],
        "georgia": [("g1", "164889003")],
    }
    for source, values in records.items():
        for name, dx in values:
            _write(raw / source / f"{name}.hea", f"{name} 12 500 5000\n#Dx: {dx}\n".encode())
            _write(raw / source / f"{name}.mat", f"waveform-{source}-{name}".encode())

    rows, _ = audit_inputs._challenge_records(
        tmp_path / "cache", config, repo, wfdb_module=FakeHeaderWFDB
    )
    excluded = {
        (row["source"], Path(row["relative_record"]).name.casefold()): row["excluded_reason"]
        for row in rows
    }

    assert excluded[("chapman_shaoxing", "c1")] == "previous_public_v45_evaluation_record"
    assert excluded[("chapman_shaoxing", "c2")] == "previous_public_v45_evaluation_record"
    assert excluded[("cpsc2018", "p1")] == "previous_public_v45_evaluation_record"
    assert excluded[("cpsc2018", "p2")] == "previous_public_v45_evaluation_record"
    assert excluded[("chapman_shaoxing", "c3")] is None
    assert excluded[("cpsc2018", "p3")] is None


def test_unreadable_wfdb_header_is_explicitly_excluded(tmp_path):
    repo = tmp_path / "repo"
    config = _write_eval_manifests(repo, [], [])
    config.update({"study_id": "test", "rhythm": {"chapman_split": {"seed": 1}}})
    raw = tmp_path / "cache/00_FUENTES_FISICAS_RAW"
    for source in audit_inputs.RHYTHM_ROOTS:
        (raw / source).mkdir(parents=True)
    header = _write(raw / "chapman_shaoxing/bad.hea", b"bad 12 500 5000\n#Dx: 164889003\n")
    _write(header.with_suffix(".mat"), b"waveform")

    class RejectingWFDB:
        @staticmethod
        def rdheader(_):
            raise ValueError("unsupported optional timestamp")

    rows, _ = audit_inputs._challenge_records(
        tmp_path / "cache", config, repo, wfdb_module=RejectingWFDB
    )
    assert len(rows) == 1
    assert rows[0]["excluded_reason"] == "invalid_wfdb_header"
    assert rows[0]["header_parse_error_type"] == "ValueError"
    assert "sample_rate_hz" not in rows[0]


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

    records, receipt = audit_inputs._ptbxl_records(
        tmp_path / "cache", config, wfdb_module=FakeHeaderWFDB
    )

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


def test_ptbxl_qc_uses_physical_directory_and_reverifies_inventory_hash(tmp_path):
    data_root = tmp_path / "cache"
    ptbxl_root = data_root / "00_FUENTES_FISICAS_RAW/ptb-xl"
    relative = "records100/00000/record_lr"
    _write(ptbxl_root / f"{relative}.hea", b"header")
    signal = _write(ptbxl_root / f"{relative}.dat", b"waveform-bytes")
    row = {
        "source": "ptbxl",
        "relative_record": relative,
        "excluded_reason": None,
        "signal_sha256": hashlib.sha256(signal.read_bytes()).hexdigest(),
    }

    class FakeWFDB:
        @staticmethod
        def rdheader(record_name):
            assert Path(record_name).is_relative_to(ptbxl_root)
            return SimpleNamespace(sig_len=20, fs=2)

        @staticmethod
        def rdrecord(record_name, *, sampfrom, sampto):
            assert Path(record_name).is_relative_to(ptbxl_root)
            assert (sampfrom, sampto) == (0, 20)
            return SimpleNamespace(p_signal=np.asarray([[0.0], [1.0]]), units=["mV"])

    result = audit_inputs._waveform_qc(
        data_root, [row], wfdb_module=FakeWFDB, verify_hash=True
    )

    assert result["ptbxl"]["records_readable"] == 1
    assert result["ptbxl"]["read_errors_by_type"] == {}
    row["signal_sha256"] = "0" * 64
    try:
        audit_inputs._waveform_qc(data_root, [row], wfdb_module=FakeWFDB, verify_hash=True)
    except audit_inputs.WaveformIntegrityError:
        pass
    else:
        raise AssertionError("changed waveform must fail closed during QC reuse")


def test_qc_reuse_preserves_source_receipt_and_inventory_hash(tmp_path, monkeypatch):
    data_root = tmp_path / "cache"
    repo = tmp_path / "repo"
    repo.mkdir()
    config_path = repo / "configs/specialist_heads/study_20261111_v2.json"
    config = _write(config_path, b'{"study_id":"test"}\n')
    monkeypatch.setattr(audit_inputs, "CONFIG", config)
    physical_root = data_root / "00_FUENTES_FISICAS_RAW/ptb-xl"
    relative = "records100/00000/record_lr"
    _write(physical_root / f"{relative}.hea", b"header")
    signal = _write(physical_root / f"{relative}.dat", b"waveform-bytes")
    inventory = {
        "schema": "TITAN_PRIVATE_SPECIALIST_INVENTORY_V1",
        "rows": [{
            "task": "pathology", "source": "ptbxl", "relative_record": relative,
            "excluded_reason": None,
            "signal_sha256": hashlib.sha256(signal.read_bytes()).hexdigest(),
        }],
    }
    source_dir = tmp_path / "previous/preflight"
    source_dir.mkdir(parents=True)
    inventory_path = _write(
        source_dir / "private_inventory.json",
        json.dumps(inventory, sort_keys=True, separators=(",", ":")).encode(),
    )
    source_receipt = {
        "schema": "TITAN_SPECIALIST_INPUT_PREFLIGHT_V1",
        "study_id": "test",
        "config_sha256": hashlib.sha256(config.read_bytes()).hexdigest(),
        "private_inventory_sha256": hashlib.sha256(inventory_path.read_bytes()).hexdigest(),
        "waveform_qc_initial_window": {"chapman_shaoxing": {"records_readable": 1}},
    }
    source_receipt_path = _write(
        source_dir / "preflight_receipt.json",
        json.dumps(source_receipt).encode(),
    )

    class FakeWFDB:
        @staticmethod
        def rdheader(record_name):
            assert Path(record_name).is_relative_to(physical_root)
            return SimpleNamespace(sig_len=20, fs=2)

        @staticmethod
        def rdrecord(record_name, *, sampfrom, sampto):
            assert Path(record_name).is_relative_to(physical_root)
            assert (sampfrom, sampto) == (0, 20)
            return SimpleNamespace(p_signal=np.asarray([[0.0], [1.0]]), units=["mV"])

    output_dir = tmp_path / "corrected/preflight"
    receipt = audit_inputs.run_qc_reuse(
        data_root, output_dir, source_dir, repo, wfdb_module=FakeWFDB
    )

    assert receipt["waveform_qc_initial_window"]["chapman_shaoxing"] == {
        "records_readable": 1
    }
    assert receipt["waveform_qc_initial_window"]["ptbxl"]["records_readable"] == 1
    assert receipt["qc_recomputation"]["source_receipt_sha256"] == hashlib.sha256(
        source_receipt_path.read_bytes()
    ).hexdigest()
    assert hashlib.sha256((output_dir / "private_inventory.json").read_bytes()).hexdigest() == (
        source_receipt["private_inventory_sha256"]
    )
