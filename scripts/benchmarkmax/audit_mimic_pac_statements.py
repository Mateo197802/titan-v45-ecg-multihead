from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from titan_v45.benchmarkmax.mimic_metadata import audit_mimic_pac_statements


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Classify approved PAC statements in MIMIC machine reports and emit aggregate counts only."
        )
    )
    parser.add_argument("--record-list", type=Path, required=True)
    parser.add_argument("--machine-measurements", type=Path, required=True)
    parser.add_argument("--mapping", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    input_paths = (args.record_list, args.machine_measurements, args.mapping)
    inputs = {path.resolve() for path in input_paths}
    if len(inputs) != 3:
        parser.error("record list, machine measurements, and mapping must be separate files")

    output_collides = args.output.resolve() in inputs
    if not output_collides and args.output.exists():
        try:
            output_collides = any(
                path.exists() and os.path.samefile(args.output, path) for path in input_paths
            )
        except OSError:
            parser.error("cannot verify that --output is separate from inputs")
    if output_collides:
        parser.error("--output must not overwrite any input or mapping")

    try:
        result = audit_mimic_pac_statements(
            args.record_list,
            args.machine_measurements,
            args.mapping,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        parser.error(f"file operation failed ({type(exc).__name__}); path details suppressed")
    except ValueError as exc:
        parser.error(f"audit validation failed ({type(exc).__name__}); details suppressed")

    counts = result["report_states"]
    print(
        "status=valid records={records} explicit_positive={positive} explicit_negative={negative} "
        "uncertain={uncertain} not_mentioned_or_missing={unmentioned}".format(
            records=result["cohort"]["matched_unique_ecgs"],
            positive=counts["explicit_positive"],
            negative=counts["explicit_negative"],
            uncertain=counts["uncertain_or_qualified"],
            unmentioned=counts["not_mentioned_or_report_missing"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
