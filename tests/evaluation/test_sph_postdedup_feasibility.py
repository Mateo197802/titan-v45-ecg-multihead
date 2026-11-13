from __future__ import annotations

import importlib.util
import io
import json
import sys
import tarfile
from pathlib import Path

import h5py
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from titan_v45.data.sph import SphMetadata  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "sph_postdedup_feasibility",
    ROOT / "scripts/benchmarkmax/audit_sph_postdedup_feasibility.py",
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def _hdf5_signal(values: np.ndarray) -> bytes:
    stream = io.BytesIO()
    with h5py.File(stream, "w") as handle:
        handle.create_dataset("ecg", data=values)
    return stream.getvalue()


def _write_archive(path: Path, records: list[tuple[str, np.ndarray]]) -> None:
    with tarfile.open(path, "w:gz") as archive:
        for record_id, values in records:
            content = _hdf5_signal(values)
            member = tarfile.TarInfo(f"{record_id}.h5")
            member.size = len(content)
            archive.addfile(member, io.BytesIO(content))


def _signal(offset: float = 0.0) -> np.ndarray:
    values = np.arange(5000, dtype=np.float32)[None, :] / 5000
    leads = np.arange(12, dtype=np.float32)[:, None]
    return values + leads + offset


def test_signal_scan_excludes_every_record_in_exact_duplicate_groups(tmp_path):
    archive = tmp_path / "signals.tar.gz"
    _write_archive(
        archive,
        [("A00001", _signal()), ("A00002", _signal()), ("A00003", _signal(2.0))],
    )

    eligible, audit = module.scan_waveform_archive(
        archive, {"A00001": 5000, "A00002": 5000, "A00003": 5000}
    )

    assert eligible == {"A00003"}
    assert audit["valid_signal_records"] == 3
    assert audit["exact_duplicate_signal_groups"] == 1
    assert audit["exact_duplicate_records_excluded"] == 2
    assert audit["unique_signal_records"] == 1


def test_support_report_uses_only_unique_eligible_records_and_exports_no_ids():
    metadata = {
        "A00001": SphMetadata("patient-shared", 5000, ((165, ()),)),
        "A00002": SphMetadata("patient-shared", 5000, ((165, ()),)),
        "A00003": SphMetadata("patient-other", 5000, ((30, ()), (142, ()))),
    }
    report = module.aggregate_support(metadata, {"A00002", "A00003"})

    serialized = json.dumps(report)
    assert "A00001" not in serialized and "patient-shared" not in serialized
    assert report["individual_identifiers_exported"] is False
    assert report["record_denominator"] == 2
    split = module.assign_split("patient-other")
    output_split = "exploratory_holdout" if split == "calibration" else split
    assert report["splits"][output_split]["records"] == 1
    assert report["splits"][output_split]["endpoints"]["PAC"]["positive_records"] == 1
    assert report["splits"][output_split]["endpoints"]["LVH"]["positive_records"] == 1


def test_label_blind_index_does_not_parse_diagnostic_columns(tmp_path):
    path = tmp_path / "metadata.csv"
    path.write_text(
        "ECG_ID,AHA_Code,Patient_ID,N\nA00001,not-consulted,P1,5000\n",
        encoding="utf-8",
    )

    assert module.read_label_blind_signal_index(path) == {"A00001": 5000}


def test_archive_scan_rejects_missing_or_unexpected_records(tmp_path):
    archive = tmp_path / "signals.tar.gz"
    _write_archive(archive, [("A00001", _signal())])

    with pytest.raises(ValueError, match="population differs"):
        module.scan_waveform_archive(
            archive, {"A00001": 5000, "A00002": 5000}
        )


def test_support_report_requires_metadata_for_each_eligible_record():
    metadata = {"A00001": SphMetadata("patient-1", 5000, ())}
    with pytest.raises(ValueError, match="not present in metadata"):
        module.aggregate_support(metadata, {"A00002"})


def test_frozen_support_configuration_is_machine_validated():
    config = json.loads(
        (ROOT / "configs/benchmarkmax/sph_postdedup_support.json").read_text(encoding="utf-8")
    )
    module._validate_config(config)


def test_historical_inventory_is_checked_against_frozen_aggregate_counts(tmp_path):
    config = json.loads(
        (ROOT / "configs/benchmarkmax/sph_postdedup_support.json").read_text(encoding="utf-8")
    )
    inventory = dict(config["source"]["source_inventory_expected"])
    inventory["primary_statement_counts"] = {
        str(code): config["source"]["source_statement_counts_before_signal_exclusions"][endpoint]
        for endpoint, (code, _) in module.TARGETS.items()
    }
    path = tmp_path / "inventory.json"
    path.write_text(json.dumps(inventory), encoding="utf-8")

    assert module.validate_source_inventory(path, config) == inventory
    inventory["valid_signal_ecgs"] -= 1
    path.write_text(json.dumps(inventory), encoding="utf-8")
    with pytest.raises(ValueError, match="valid_signal_ecgs"):
        module.validate_source_inventory(path, config)
