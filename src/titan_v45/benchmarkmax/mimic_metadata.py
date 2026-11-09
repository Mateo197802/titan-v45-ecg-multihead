"""Aggregate-only validation of MIMIC-IV-ECG metadata joins."""
from __future__ import annotations

import csv
import hashlib
import json
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

REPORT_COLUMNS = tuple(f"report_{index}" for index in range(18))
RECORD_COLUMNS = ("path", "subject_id", "study_id")
MEASUREMENT_COLUMNS = ("subject_id", "study_id", *REPORT_COLUMNS)
AUDIT_SCHEMA = "TITAN_V46_MIMIC_METADATA_AUDIT_V1"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@contextmanager
def _reader(path: Path, required: tuple[str, ...]) -> Iterator[csv.DictReader[str]]:
    stream = path.open("r", encoding="utf-8-sig", newline="")
    try:
        reader = csv.DictReader(stream)
        headers = reader.fieldnames
        if headers is None:
            raise ValueError(f"CSV has no header: {path.name}")
        if len(headers) != len(set(headers)):
            raise ValueError(f"CSV has duplicate column names: {path.name}")
        missing = [column for column in required if column not in headers]
        if missing:
            expected = "record_list fields" if required == RECORD_COLUMNS else "report_0..report_17"
            raise ValueError(f"{path.name} is missing required {expected}")
        yield reader
    finally:
        stream.close()


def _key(row: dict[str | None, str | None]) -> tuple[str, str]:
    subject_id = row.get("subject_id")
    study_id = row.get("study_id")
    if not subject_id or not subject_id.strip() or not study_id or not study_id.strip():
        raise ValueError("metadata rows require non-empty subject_id and study_id")
    return subject_id.strip(), study_id.strip()


def _report_signature(row: dict[str | None, str | None]) -> bytes:
    lines: list[str] = []
    for column in REPORT_COLUMNS:
        value = row.get(column)
        if value is None:
            raise ValueError(f"metadata row is missing a value for {column}")
        lines.append(value)
    canonical = json.dumps(lines, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).digest()


def audit_mimic_metadata(record_list_path: Path, machine_measurements_path: Path) -> dict[str, Any]:
    """Validate metadata keys and report coverage without exporting row-level data."""
    record_list_path = Path(record_list_path)
    machine_measurements_path = Path(machine_measurements_path)
    if record_list_path.resolve() == machine_measurements_path.resolve():
        raise ValueError("record_list and machine_measurements must be separate files")

    record_keys: set[tuple[str, str]] = set()
    record_patients: set[str] = set()
    record_rows = 0
    record_duplicates = 0
    with _reader(record_list_path, RECORD_COLUMNS) as reader:
        for row in reader:
            if row.get(None) is not None:
                raise ValueError("record_list row has unexpected extra fields")
            if row.get("path") is None or not row["path"].strip():
                raise ValueError("record_list rows require a non-empty path")
            key = _key(row)
            record_rows += 1
            record_patients.add(key[0])
            if key in record_keys:
                record_duplicates += 1
            else:
                record_keys.add(key)
    measurement_keys: set[tuple[str, str]] = set()
    measurement_patients: set[str] = set()
    report_signatures: dict[tuple[str, str], bytes] = {}
    conflicting_report_keys: set[tuple[str, str]] = set()
    measurement_rows = 0
    measurement_duplicates = 0
    rows_with_text = 0
    rows_without_text = 0
    with _reader(machine_measurements_path, MEASUREMENT_COLUMNS) as reader:
        for row in reader:
            if row.get(None) is not None:
                raise ValueError("machine_measurements row has unexpected extra fields")
            key = _key(row)
            signature = _report_signature(row)
            measurement_rows += 1
            measurement_patients.add(key[0])
            if any((row.get(column) or "").strip() for column in REPORT_COLUMNS):
                rows_with_text += 1
            else:
                rows_without_text += 1
            if key in measurement_keys:
                measurement_duplicates += 1
                if report_signatures[key] != signature:
                    conflicting_report_keys.add(key)
            else:
                measurement_keys.add(key)
                report_signatures[key] = signature

    matched = record_keys & measurement_keys
    record_only = record_keys - measurement_keys
    measurement_only = measurement_keys - record_keys
    valid = bool(record_rows and measurement_rows) and not any(
        (
            record_duplicates,
            measurement_duplicates,
            conflicting_report_keys,
            record_only,
            measurement_only,
        )
    )

    return {
        "schema": AUDIT_SCHEMA,
        "dataset_version": "1.0",
        "status": "valid" if valid else "invalid",
        "input_sha256": {
            "record_list.csv": _sha256(record_list_path),
            "machine_measurements.csv": _sha256(machine_measurements_path),
        },
        "record_list": {
            "rows": record_rows,
            "unique_ecgs": len(record_keys),
            "unique_patients": len(record_patients),
            "duplicate_key_rows": record_duplicates,
        },
        "machine_measurements": {
            "rows": measurement_rows,
            "unique_ecgs": len(measurement_keys),
            "unique_patients": len(measurement_patients),
            "duplicate_key_rows": measurement_duplicates,
            "conflicting_report_keys": len(conflicting_report_keys),
            "rows_with_any_report_text": rows_with_text,
            "rows_with_no_report_text": rows_without_text,
        },
        "join": {
            "matched_unique_ecgs": len(matched),
            "record_list_only_unique_ecgs": len(record_only),
            "machine_measurements_only_unique_ecgs": len(measurement_only),
        },
        "policy": {
            "report_phrase_mapping_applied": False,
            "report_silence_is_negative": False,
            "waveform_inference_performed": False,
            "row_level_data_exported": False,
        },
    }
