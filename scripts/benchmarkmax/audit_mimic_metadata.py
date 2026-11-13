from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from titan_v45.benchmarkmax.mimic_metadata import audit_mimic_metadata


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate MIMIC-IV-ECG metadata joins and emit aggregate counts only."
    )
    parser.add_argument("--record-list", type=Path, required=True)
    parser.add_argument("--machine-measurements", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    inputs = {args.record_list.resolve(), args.machine_measurements.resolve()}
    if args.output.resolve() in inputs:
        parser.error("--output must not overwrite either input file")
    try:
        result = audit_mimic_metadata(args.record_list, args.machine_measurements)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    print(
        "status={status} records={records} measurements={measurements} matched={matched}".format(
            status=result["status"],
            records=result["record_list"]["rows"],
            measurements=result["machine_measurements"]["rows"],
            matched=result["join"]["matched_unique_ecgs"],
        )
    )
    return 0 if result["status"] == "valid" else 2


if __name__ == "__main__":
    raise SystemExit(main())
