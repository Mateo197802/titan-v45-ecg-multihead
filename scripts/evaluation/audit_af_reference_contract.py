"""Audit P6/P8 ECG-associated AF flags by literal source label, without exporting IDs."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from titan_v45.evaluation.label_reference import audit_af_reference_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    results = {}
    inputs = []
    for profile, field in [("primary6", "true_labels"), ("primary8", "accepted_labels")]:
        path = ROOT / f"outputs/results/external_dev/evidence/rhythm_{profile}_record_predictions.csv"
        inputs.append(path)
        if args.output.resolve() == path.resolve() or (args.output.exists() and args.output.samefile(path)):
            raise ValueError("output aliases a prediction input")
        raw = path.read_bytes()
        rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
        results[profile] = audit_af_reference_rows(rows, reference_field=field)
        results[profile]["input_sha256"] = hashlib.sha256(raw).hexdigest()
    result = {"profiles": results, "reference_code": "164889003", "normal_rhythm_code": "426783006",
              "source_labels_are_not_independent_institutions": True,
              "limitations": ["Code/accepted-label agreement does not adjudicate the original diagnosis.",
                              "No event dates, incidence, first diagnosis or patient split independence established.",
                              "A co-occurring AF/NSR code set is reported, not silently adjudicated or relabeled."]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes((json.dumps(result, indent=2) + "\n").encode())


if __name__ == "__main__":
    main()
