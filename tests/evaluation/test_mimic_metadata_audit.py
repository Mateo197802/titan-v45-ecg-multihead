from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

from titan_v45.benchmarkmax.mimic_metadata import audit_mimic_metadata

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/benchmarkmax/audit_mimic_metadata.py"


def _write_csv(path: Path, columns: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _record_row(subject: str, study: str) -> dict[str, str]:
    return {
        "path": f"files/p{subject[:4]}/p{subject}/s{study}/{study}",
        "subject_id": subject,
        "study_id": study,
    }


def _measurement_row(subject: str, study: str, *reports: str) -> dict[str, str]:
    row = {f"report_{index}": "" for index in range(18)}
    row.update({"subject_id": subject, "study_id": study})
    for index, report in enumerate(reports):
        row[f"report_{index}"] = report
    return row


def _inputs(tmp_path: Path) -> tuple[Path, Path]:
    records = tmp_path / "record_list.csv"
    measurements = tmp_path / "machine_measurements.csv"
    _write_csv(records, ["path", "subject_id", "study_id"], [])
    _write_csv(
        measurements,
        ["subject_id", "study_id", *(f"report_{index}" for index in range(18))],
        [],
    )
    return records, measurements


def test_metadata_audit_returns_aggregate_counts_without_ids_or_report_text(
    tmp_path: Path,
) -> None:
    records, measurements = _inputs(tmp_path)
    _write_csv(
        records,
        ["path", "subject_id", "study_id"],
        [_record_row("subject-A", "study-1"), _record_row("subject-A", "study-2")],
    )
    _write_csv(
        measurements,
        ["subject_id", "study_id", *(f"report_{index}" for index in range(18))],
        [
            _measurement_row("subject-A", "study-1", "SYNTHETIC PAC PHRASE"),
            _measurement_row("subject-A", "study-2"),
        ],
    )

    result = audit_mimic_metadata(records, measurements)
    serialized = json.dumps(result)

    assert result["status"] == "valid"
    assert result["record_list"]["rows"] == 2
    assert result["record_list"]["unique_patients"] == 1
    assert result["machine_measurements"]["rows_with_any_report_text"] == 1
    assert result["machine_measurements"]["rows_with_no_report_text"] == 1
    assert result["join"]["matched_unique_ecgs"] == 2
    assert "subject-A" not in serialized
    assert "study-1" not in serialized
    assert "SYNTHETIC PAC PHRASE" not in serialized
    assert "report_0" not in serialized


def test_metadata_audit_counts_duplicate_conflicts_and_unmatched_keys(
    tmp_path: Path,
) -> None:
    records, measurements = _inputs(tmp_path)
    _write_csv(
        records,
        ["path", "subject_id", "study_id"],
        [
            _record_row("subject-A", "study-1"),
            _record_row("subject-A", "study-1"),
            _record_row("subject-B", "study-2"),
        ],
    )
    _write_csv(
        measurements,
        ["subject_id", "study_id", *(f"report_{index}" for index in range(18))],
        [
            _measurement_row("subject-A", "study-1", "SYNTHETIC POSITIVE"),
            _measurement_row("subject-A", "study-1", "SYNTHETIC NEGATIVE"),
            _measurement_row("subject-C", "study-3"),
        ],
    )

    result = audit_mimic_metadata(records, measurements)

    assert result["status"] == "invalid"
    assert result["record_list"]["duplicate_key_rows"] == 1
    assert result["machine_measurements"]["duplicate_key_rows"] == 1
    assert result["machine_measurements"]["conflicting_report_keys"] == 1
    assert result["join"]["matched_unique_ecgs"] == 1
    assert result["join"]["record_list_only_unique_ecgs"] == 1
    assert result["join"]["machine_measurements_only_unique_ecgs"] == 1


def test_metadata_audit_rejects_missing_report_slots(tmp_path: Path) -> None:
    records, measurements = _inputs(tmp_path)
    _write_csv(records, ["path", "subject_id", "study_id"], [])
    _write_csv(
        measurements,
        ["subject_id", "study_id", *(f"report_{index}" for index in range(17))],
        [],
    )

    with pytest.raises(ValueError, match="report_0..report_17"):
        audit_mimic_metadata(records, measurements)


def test_metadata_audit_does_not_mark_empty_tables_valid(tmp_path: Path) -> None:
    records, measurements = _inputs(tmp_path)

    result = audit_mimic_metadata(records, measurements)

    assert result["record_list"]["rows"] == 0
    assert result["machine_measurements"]["rows"] == 0
    assert result["status"] == "invalid"


def test_metadata_audit_rejects_empty_join_keys(tmp_path: Path) -> None:
    records, measurements = _inputs(tmp_path)
    _write_csv(records, ["path", "subject_id", "study_id"], [_record_row("", "study-1")])
    _write_csv(
        measurements,
        ["subject_id", "study_id", *(f"report_{index}" for index in range(18))],
        [],
    )

    with pytest.raises(ValueError, match="non-empty subject_id and study_id"):
        audit_mimic_metadata(records, measurements)


def test_metadata_audit_cli_writes_only_the_aggregate_report(tmp_path: Path) -> None:
    records, measurements = _inputs(tmp_path)
    _write_csv(
        records,
        ["path", "subject_id", "study_id"],
        [_record_row("private-subject", "private-study")],
    )
    _write_csv(
        measurements,
        ["subject_id", "study_id", *(f"report_{index}" for index in range(18))],
        [_measurement_row("private-subject", "private-study", "SYNTHETIC REPORT TEXT")],
    )
    output = tmp_path / "aggregate.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--record-list",
            str(records),
            "--machine-measurements",
            str(measurements),
            "--output",
            str(output),
        ],
        capture_output=True,
        check=False,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    aggregate = output.read_text(encoding="utf-8")
    assert json.loads(aggregate)["status"] == "valid"
    assert "private-subject" not in aggregate
    assert "private-study" not in aggregate
    assert "SYNTHETIC REPORT TEXT" not in aggregate
