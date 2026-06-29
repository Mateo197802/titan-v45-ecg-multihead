from __future__ import annotations

import csv
import json
from pathlib import Path

from titan_v45.artifacts.sanitize import sanitize_report_file


def test_sanitize_csv_rewrites_record_paths_and_redacts_private_values(tmp_path: Path) -> None:
    source = tmp_path / "predictions.csv"
    with source.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["record_id", "source", "record_base", "header_path", "note"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "record_id": "A0001",
                "source": "Private Source",
                "record_base": "C:" + "\\Users\\person\\records\\A0001",
                "header_path": "C:" + "\\Users\\person\\records\\A0001.hea",
                "note": "/" + "home/private/run/file.txt",
            }
        )
    destination = tmp_path / "sanitized.csv"

    sanitize_report_file(source, destination)

    text = destination.read_text(encoding="utf-8")
    assert "C:" + "\\Users" not in text
    assert "/" + "home/private" not in text
    assert "records/private-source/A0001/A0001" in text
    assert "<PRIVATE_PATH_REDACTED>" in text


def test_sanitize_json_redacts_private_paths_recursively(tmp_path: Path) -> None:
    source = tmp_path / "report.json"
    source.write_text(
        json.dumps(
            {
                "path": "/" + "home/private/run/model.pt",
                "nested": ["C:" + "\\Users\\x\\a.pt"],
            }
        ),
        encoding="utf-8",
    )
    destination = tmp_path / "sanitized.json"

    sanitize_report_file(source, destination)

    payload = json.loads(destination.read_text(encoding="utf-8"))
    assert payload == {"path": "<PRIVATE_PATH_REDACTED>", "nested": ["<PRIVATE_PATH_REDACTED>"]}
