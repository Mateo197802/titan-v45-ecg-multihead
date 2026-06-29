from __future__ import annotations

import csv
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any

PRIVATE_PATH = re.compile(
    r"(?:[A-Za-z]:[\\/]+Users[\\/]+[^,\s]+|/" + r"home/[^,\s]+|/Users/[^,\s]+)"
)


def _slug(value: str, fallback: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-._").lower()
    return normalized or fallback


def _safe_identifier(value: str, fallback: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-._")
    return normalized or fallback


def _basename(value: str) -> str:
    normalized = value.replace("\\", "/").rstrip("/")
    return normalized.rsplit("/", maxsplit=1)[-1] or "record"


def _public_record_path(row: dict[str, str], original: str, *, suffix: str = "") -> str:
    source = _slug(row.get("source") or row.get("source_family") or "external-dev", "external-dev")
    record_id = _safe_identifier(row.get("record_id") or _basename(original), "record")
    basename = _basename(original)
    if suffix and not basename.endswith(suffix):
        basename += suffix
    return PurePosixPath("records", source, record_id, basename).as_posix()


def _sanitize_string(value: str) -> str:
    if PRIVATE_PATH.search(value):
        return "<PRIVATE_PATH_REDACTED>"
    return value


def _sanitize_csv(source: Path, destination: Path) -> None:
    with source.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
        fieldnames = handle.seek(0) or next(csv.reader(handle))
    sanitized_rows: list[dict[str, str]] = []
    for row in rows:
        sanitized: dict[str, str] = {}
        for key, value in row.items():
            value = "" if value is None else str(value)
            if key in {"record", "record_base"} and PRIVATE_PATH.search(value):
                sanitized[key] = _public_record_path(row, value)
            elif key == "header_path" and PRIVATE_PATH.search(value):
                sanitized[key] = _public_record_path(row, value)
            else:
                sanitized[key] = _sanitize_string(value)
        sanitized_rows.append(sanitized)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(sanitized_rows)


def _sanitize_json_value(value: Any) -> Any:
    if isinstance(value, str):
        return _sanitize_string(value)
    if isinstance(value, list):
        return [_sanitize_json_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _sanitize_json_value(item) for key, item in value.items()}
    return value


def _sanitize_json(source: Path, destination: Path) -> None:
    payload = json.loads(source.read_text(encoding="utf-8"))
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(_sanitize_json_value(payload), indent=2) + "\n",
        encoding="utf-8",
    )


def sanitize_report_file(source: str | Path, destination: str | Path) -> None:
    source_path = Path(source)
    destination_path = Path(destination)
    suffix = source_path.suffix.lower()
    if suffix == ".csv":
        _sanitize_csv(source_path, destination_path)
    elif suffix == ".json":
        _sanitize_json(source_path, destination_path)
    else:
        raise ValueError(f"unsupported report type: {source_path.suffix}")
