"""Audit source checksums offline. Exit 0 means audit completed, not all records verified."""
from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from titan_v45.evaluation.source_checksums import audit_source_checksums


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--checksums", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="Aggregate JSON, without record IDs")
    parser.add_argument("--details", type=Path, help="Opt-in .json/.csv containing record IDs, never headers")
    args = parser.parse_args()
    try:
        outputs = [args.output] + ([args.details] if args.details else [])
        resolved = [p.resolve() for p in outputs]
        if len(set(resolved)) != len(resolved) or set(resolved) & {
            args.inventory.resolve(), args.checksums.resolve()
        }:
            raise ValueError("output paths must differ from inputs and each other")
        for i, path in enumerate(outputs):
            others = [args.inventory, args.checksums, *outputs[:i]]
            if path.exists() and any(p.exists() and path.samefile(p) for p in others):
                raise ValueError("output aliases an input or another output")
        if args.details and args.details.suffix.lower() not in {".json", ".csv"}:
            raise ValueError("details extension must be .json or .csv")
        report, details = audit_source_checksums(args.inventory, args.checksums)
        serialized = [json.dumps(report, indent=2) + "\n"]
        if args.details:
            if args.details.suffix.lower() == ".json":
                serialized.append(json.dumps(details, indent=2) + "\n")
            else:
                buffer = io.StringIO(newline="")
                columns = ["record_id", "mat_bytes", "mat_sha256", "hea_bytes", "hea_sha256", "status",
                           "signal_status", "header_status", "matches", "selected_match_path", "verified_source"]
                writer = csv.DictWriter(buffer, fieldnames=columns, lineterminator="\n")
                writer.writeheader()
                writer.writerows({**row, "matches": json.dumps(row["matches"], sort_keys=True)} for row in details)
                serialized.append(buffer.getvalue())
        for path, text in zip(outputs, serialized, strict=True):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(text.encode("utf-8"))
    except (OSError, TypeError, ValueError) as exc:
        print(f"Source checksum audit failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
