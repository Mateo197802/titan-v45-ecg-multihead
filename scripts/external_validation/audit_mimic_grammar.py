"""Count audited grammar patterns on the fixed MIMIC development subset only."""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

from fit_code_transfer import digest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from titan_v45.data.external_reference import REPORT_COLUMNS, _normalized, classify_report

# Patterns only, not exported source text or labels assigned by a revised parser.
PATTERNS = {
    "AV_BLOCK_A_V_VARIANT": ("1AVB", r"\b(?:first|1st) degree a v block\b"),
    "AV_BLOCK_COMPOUND": ("1AVB", r"\b(?:first|1st) degree (?:av|a v|atrioventricular) block\b"),
    "RBBB_ABBREVIATION": ("RBBB", r"\brbbb\b"),
    "LVH_VOLTAGE_QUALIFIER": ("LVH", r"\b(?:voltage criteria|minimal voltage)\b.*\b(?:lvh|left ventricular hypertrophy)\b"),
    "AF_COMPOUND": ("AFIB", r"\batrial fibrillation (?:with|and)\b"),
    "SINUS_COMPOUND": ("NSR", r"\bsinus rhythm (?:with|and)\b"),
    "INFERIOR_AGE_UNDETERMINED": ("IMI", r"\binferior infarct\b.*\bage undetermined\b"),
}


def run(study: Path, out: Path):
    meta = study / "mimic/machine_measurements.csv"
    if digest(meta) != "56f6b1413221bce95bd6f48b28ca1acf27ae0b073d6f2c1d12f3af7500eabbb6":
        raise ValueError("MIMIC machine metadata changed")
    selection = [json.loads(line) for line in (study / "private_mimic_selection.jsonl").read_bytes().splitlines()]
    development = {row["study_id"]: row["subject_id"] for row in selection if row["split"] in
                   {"train", "validation", "calibration"}}
    states: dict[str, Counter] = {}
    patterns: dict[str, Counter] = {name: Counter() for name in PATTERNS}
    seen = set()
    with meta.open(encoding="utf-8-sig", errors="replace", newline="") as stream:
        for row in csv.DictReader(stream):
            key = row["study_id"]
            if key not in development:
                continue
            if row["subject_id"] != development[key] or key in seen:
                raise ValueError("unexpected development join")
            seen.add(key)
            labels = classify_report(row)
            for endpoint, state in labels.items():
                states.setdefault(endpoint, Counter())[state] += 1
            lines = [_normalized(row[column] or "") for column in REPORT_COLUMNS]
            for name, (endpoint, pattern) in PATTERNS.items():
                if any(re.search(pattern, line) for line in lines):
                    patterns[name][labels[endpoint]] += 1
    if seen != development.keys():
        raise ValueError("incomplete development join")
    result = {"development_ecgs": len(seen), "retained_labels_extracted": False,
              "counts": states, "patterns_by_original_state": patterns,
              "proportions": {endpoint: {key: count / len(seen) for key, count in counters.items()}
                              for endpoint, counters in states.items()},
              "interpretation": "Parser state coverage, not independently adjudicated accuracy."}
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    out.write_bytes(encoded.encode())
    print(encoded, end="")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("study", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    run(args.study, args.output)
