from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from titan_v45.benchmarkmax import mimic_metadata

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/benchmarkmax/audit_mimic_pac_statements.py"
REPORT_COLUMNS = [f"report_{index}" for index in range(18)]
RECORD_COLUMNS = ["path", "subject_id", "study_id"]
MEASUREMENT_COLUMNS = ["subject_id", "study_id", *REPORT_COLUMNS]


def _write_csv(path: Path, columns: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _record(subject: str, study: str) -> dict[str, str]:
    return {
        "path": f"private/files/{subject}/{study}",
        "subject_id": subject,
        "study_id": study,
    }


def _measurement(subject: str, study: str, first_report: str = "") -> dict[str, str]:
    row = {column: "" for column in MEASUREMENT_COLUMNS}
    row.update({"subject_id": subject, "study_id": study, "report_0": first_report})
    return row


def _mapping(*, status: str = "approved_by_corresponding_author") -> dict[str, object]:
    approval = (
        {"approved_by": "Synthetic test fixture", "approved_on": "2026-11-09"}
        if status == "approved_by_corresponding_author"
        else None
    )
    return {
        "schema": "TITAN_V46_MIMIC_PAC_REPORT_MAPPING_V1",
        "mapping_id": "synthetic-audit-test",
        "status": status,
        "approval": approval,
        "phrases": {
            "explicit_positive": ["PAC", "PACs"],
            "explicit_negative": ["no PAC", "no PACs"],
            "uncertain_or_qualified": ["possible PAC", "cannot exclude PAC"],
        },
    }


def _inputs(tmp_path: Path) -> tuple[Path, Path, list[dict[str, str]], list[dict[str, str]]]:
    records = [
        _record("private-subject-A", "private-study-1"),
        _record("private-subject-A", "private-study-2"),
        _record("private-subject-B", "private-study-3"),
        _record("private-subject-B", "private-study-4"),
    ]
    measurements = [
        _measurement("private-subject-A", "private-study-1", "PAC present"),
        _measurement("private-subject-A", "private-study-2", "No PAC"),
        _measurement("private-subject-B", "private-study-3", "Possible PAC"),
        _measurement("private-subject-B", "private-study-4", "Normal sinus rhythm"),
    ]
    record_path = tmp_path / "record_list.csv"
    measurements_path = tmp_path / "machine_measurements.csv"
    _write_csv(record_path, RECORD_COLUMNS, records)
    _write_csv(measurements_path, MEASUREMENT_COLUMNS, measurements)
    return record_path, measurements_path, records, measurements


def _write_mapping(tmp_path: Path, data: dict[str, object]) -> Path:
    path = tmp_path / "mapping.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_pac_statement_audit_emits_only_approved_aggregate_states(tmp_path: Path) -> None:
    record_path, measurements_path, _, _ = _inputs(tmp_path)
    mapping_path = _write_mapping(tmp_path, _mapping())

    result = mimic_metadata.audit_mimic_pac_statements(
        record_path, measurements_path, mapping_path
    )
    serialized = json.dumps(result)

    assert result["status"] == "valid"
    assert result["cohort"] == {
        "matched_unique_ecgs": 4,
        "unique_patients": 2,
        "rows_with_any_report_text": 4,
        "rows_with_no_report_text": 0,
    }
    assert result["report_states"] == {
        "explicit_positive": 1,
        "explicit_negative": 1,
        "uncertain_or_qualified": 1,
        "not_mentioned_or_report_missing": 1,
    }
    assert result["policy"]["clinical_reference"] is False
    assert result["policy"]["silence_is_explicit_negative"] is False
    assert result["policy"]["model_inference_performed"] is False
    assert result["policy"]["row_level_data_exported"] is False
    for private_value in (
        "private-subject-A",
        "private-study-1",
        "Normal sinus rhythm",
        str(record_path),
        str(measurements_path),
        "report_0",
    ):
        assert private_value not in serialized


def test_pending_mapping_is_rejected_before_statement_audit(tmp_path: Path) -> None:
    record_path, measurements_path, _, _ = _inputs(tmp_path)
    mapping_path = _write_mapping(tmp_path, _mapping(status="pending_author_approval"))

    with pytest.raises(ValueError, match="author approval"):
        mimic_metadata.audit_mimic_pac_statements(
            record_path, measurements_path, mapping_path
        )


def test_invalid_metadata_join_aborts_classification(tmp_path: Path) -> None:
    record_path, measurements_path, records, measurements = _inputs(tmp_path)
    _write_csv(record_path, RECORD_COLUMNS, records[:-1])
    mapping_path = _write_mapping(tmp_path, _mapping())

    with pytest.raises(ValueError, match="metadata join is invalid"):
        mimic_metadata.audit_mimic_pac_statements(
            record_path, measurements_path, mapping_path
        )


def test_cli_rejects_output_overwrite_and_does_not_write_on_pending_mapping(
    tmp_path: Path,
) -> None:
    record_path, measurements_path, _, _ = _inputs(tmp_path)
    pending_mapping = _write_mapping(tmp_path, _mapping(status="pending_author_approval"))
    collision = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--record-list",
            str(record_path),
            "--machine-measurements",
            str(measurements_path),
            "--mapping",
            str(pending_mapping),
            "--output",
            str(record_path),
        ],
        capture_output=True,
        check=False,
        text=True,
    )
    assert collision.returncode == 2
    assert "must not overwrite" in collision.stderr

    output = tmp_path / "private-output.json"
    rejected = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--record-list",
            str(record_path),
            "--machine-measurements",
            str(measurements_path),
            "--mapping",
            str(pending_mapping),
            "--output",
            str(output),
        ],
        capture_output=True,
        check=False,
        text=True,
    )
    assert rejected.returncode == 2
    assert not output.exists()
    assert "private-subject-A" not in rejected.stdout + rejected.stderr


def test_cli_rejects_hard_link_alias_to_an_input(tmp_path: Path) -> None:
    record_path, measurements_path, _, _ = _inputs(tmp_path)
    mapping_path = _write_mapping(tmp_path, _mapping())
    hard_link = tmp_path / "record-list-alias.csv"
    try:
        os.link(record_path, hard_link)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"hard links are unavailable in this test environment: {exc}")
    original = record_path.read_bytes()

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--record-list",
            str(record_path),
            "--machine-measurements",
            str(measurements_path),
            "--mapping",
            str(mapping_path),
            "--output",
            str(hard_link),
        ],
        capture_output=True,
        check=False,
        text=True,
    )

    assert completed.returncode == 2
    assert "must not overwrite" in completed.stderr
    assert record_path.read_bytes() == original


def test_cli_suppresses_private_paths_from_file_errors(tmp_path: Path) -> None:
    record_path, _, _, _ = _inputs(tmp_path)
    missing_measurements = tmp_path / "private-source-folder" / "missing.csv"
    mapping_path = _write_mapping(tmp_path, _mapping())
    output = tmp_path / "aggregate.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--record-list",
            str(record_path),
            "--machine-measurements",
            str(missing_measurements),
            "--mapping",
            str(mapping_path),
            "--output",
            str(output),
        ],
        capture_output=True,
        check=False,
        text=True,
    )

    assert completed.returncode == 2
    assert str(tmp_path) not in completed.stderr
    assert "path details suppressed" in completed.stderr
    assert not output.exists()
