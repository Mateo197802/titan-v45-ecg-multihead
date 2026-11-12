"""Audit MIMIC development-reference coverage without loading retained outcomes."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from acquire_mimic import atomic, checksum_index, select

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from titan_v45.data.external_reference import REPORT_COLUMNS, classify_report


def run(root: Path, protocol: Path) -> dict:
    mimic = root / "mimic"
    metadata_names = {"record_list.csv", "machine_measurements.csv"}
    checksums = checksum_index(mimic / "SHA256SUMS.txt", metadata_names)
    for filename in metadata_names:
        digest = hashlib.sha256()
        with (mimic / filename).open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        if digest.hexdigest() != checksums[filename]:
            raise ValueError(f"publisher hash mismatch: {filename}")
    protocol_bytes = protocol.read_bytes()
    config = json.loads(protocol_bytes)["mimic_acquisition"]
    with (mimic / "record_list.csv").open(newline="", encoding="utf-8-sig") as stream:
        selected = {
            r["study_id"]: r for r in select(csv.DictReader(stream), seed=config["seed"],
                                             patient_limit=config["patient_limit"],
                                             max_records=config["max_records_per_patient"])
            if r["split"] != "test"
        }
    counts = defaultdict(lambda: defaultdict(Counter))
    patients = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))
    cohort_counts = Counter(row["split"] for row in selected.values())
    seen = set()
    with (mimic / "machine_measurements.csv").open("rb") as stream:
        # Replace invalid UTF-8 rather than dropping rows; malformed clauses remain unknown.
        reader = csv.DictReader(io.TextIOWrapper(stream, encoding="utf-8-sig", errors="replace", newline=""))
        if not set(REPORT_COLUMNS).issubset(reader.fieldnames or ()):
            raise ValueError("missing machine report columns")
        for row in reader:
            study = row["study_id"]
            if study not in selected:
                continue
            link = selected[study]
            if link["subject_id"] != row["subject_id"] or study in seen:
                raise ValueError("ambiguous development report join")
            seen.add(study)
            for endpoint, state in classify_report(row).items():
                counts[link["split"]][endpoint][state] += 1
                if state in {"positive", "explicit_negative"}:
                    patients[link["split"]][endpoint][state].add(link["subject_id"])
    matched = Counter(selected[study]["split"] for study in seen)
    gate_bytes = (ROOT / "docs/external_validation_20261111/REFERENCE_AUDIT_GATE.json").read_bytes()
    minima = json.loads(gate_bytes)["per_endpoint_minimum_distinct_patients_per_polarity"]
    support = {}
    endpoints = sorted(set().union(*(set(counts[split]) for split in minima)))
    for endpoint in endpoints:
        by_split = {}
        for split in minima:
            pos = patients[split][endpoint]["positive"]
            neg = patients[split][endpoint]["explicit_negative"]
            by_split[split] = {"positive": len(pos - neg), "explicit_negative": len(neg - pos)}
        support[endpoint] = by_split
    passed = [endpoint for endpoint, splits in support.items()
              if all(min(values.values()) >= minima[split] for split, values in splits.items())]
    receipt = {
        "scope": "DEVELOPMENT_MACHINE_STATEMENT_SUPPORT_ONLY",
        "protocol_sha256": hashlib.sha256(protocol_bytes).hexdigest(),
        "reference_code_sha256": hashlib.sha256(
            (ROOT / "src/titan_v45/data/external_reference.py").read_bytes()
        ).hexdigest(),
        "publisher_verified_metadata": checksums,
        "selected_development_ecgs": dict(cohort_counts),
        "joined_development_ecgs": dict(matched),
        "report_columns": len(REPORT_COLUMNS),
        "states_by_split_and_endpoint": counts,
        "patient_support_by_split_and_endpoint": support,
        "reference_audit_gate_sha256": hashlib.sha256(gate_bytes).hexdigest(),
        "endpoints_passing_development_support": passed,
        "test_labels_extracted": False,
        "performance_computed": False,
    }
    atomic(root / "private_mimic_reference_audit.json", (json.dumps(receipt, indent=2) + "\n").encode())
    private_fields = {"states_by_split_and_endpoint", "patient_support_by_split_and_endpoint"}
    print(json.dumps({k: v for k, v in receipt.items() if k not in private_fields}, indent=2))
    return receipt


if __name__ == "__main__":
    import os

    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("protocol", type=Path)
    args = parser.parse_args()
    run(args.root, args.protocol)
