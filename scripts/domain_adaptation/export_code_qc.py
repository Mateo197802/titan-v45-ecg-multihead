"""Export allow-listed aggregate CODE QC, never per-record labels or keys."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "docs/domain_adaptation/MULTISOURCE_TRAINING_PROTOCOL.json"
SPLITS = ("train", "validation", "calibration", "test")
REASONS = {"all_zero", "ambiguous_duration", "exact_waveform_cross_split", "exact_waveform_within_split", "flat_lead"}


def seal(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def export(receipt, output):
    raw = json.loads(receipt.read_bytes())
    if raw["protocol_sha256"] != seal(POLICY) or raw["patient_overlap"] != 0 or not raw["exclusions"].keys() <= REASONS:
        raise ValueError("incompatible QC receipt")
    cohort = []
    for split in SPLITS:
        group = raw["splits"][split]
        count = [group["ecgs"], group["patients"], group["duration"].get("short_7p335", 0),
                 group["duration"].get("long_10", 0), group["historical_pr6_patients"]]
        if any(type(v) is not int or v < 0 for v in count) or not (
            0 < count[1] <= count[0] <= 2 * count[1] and count[2] + count[3] == count[0]
            and count[4] <= count[1] and (split == "train" or count[4] == 0)
        ):
            raise ValueError("invalid split denominator")
        cohort.append(("CODE-15%", split, *count))
    if any(type(v) is not int or v < 0 for v in raw["exclusions"].values()) or (
        sum(row[2] for row in cohort) + sum(raw["exclusions"].values()) != raw["planned_ecgs"]
    ):
        raise ValueError("inconsistent exclusions")
    counts = output / "EXTERNAL_DATA_MANIFESTS_SUMMARY.csv"
    with counts.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(("source", "split", "ecgs", "patients", "short_7p335_ecgs", "long_10_ecgs", "pr6_exposed_patients"))
        writer.writerows(cohort)
    qc = {"scope": "WITHIN_CODE_ONLY", "full_qc_receipt_sha256": seal(receipt), "protocol_sha256": seal(POLICY),
          "public_cohort_counts_sha256": seal(counts), "exclusions": raw["exclusions"], "patient_overlap": 0,
          "exact_overlap_screen": "observed float32 waveform within CODE; not an inter-provider patient check",
          "independent_institutional_evaluation": False, "per_record_data_exported": False,
          "reserved_test_endpoint_counts_exported": False}
    (output / "PATIENT_AND_SIGNAL_LEAKAGE_AUDIT.json").write_bytes((json.dumps(qc, sort_keys=True, indent=2) + "\n").encode())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    export(args.receipt, args.output)
