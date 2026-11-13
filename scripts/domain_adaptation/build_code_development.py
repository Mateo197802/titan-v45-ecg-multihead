"""Build a bounded patient-disjoint CODE development waveform bank on CEDIA."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

import h5py
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/external_validation"))
from code15_io import digest
from evaluate_code15 import label, selected, verified_hdf5

from titan_v45.data.duration_aware_preprocessing import (
    code_observed_window,
    observed_descriptors,
    prepare_observed,
)

PROTOCOL = ROOT / "docs/domain_adaptation/MULTISOURCE_TRAINING_PROTOCOL.json"
SPLITS = ("train", "validation", "calibration", "test")


def stable(seed, value):
    return hashlib.sha256(f"{seed}|{value}".encode()).digest()


def assign(patient, config):
    bucket = int.from_bytes(stable(config["assignment_seed"], patient)[:8], "big") % 100
    return next(split for split, cutoff in zip(SPLITS, config["split_cutoffs_percent"], strict=True) if bucket < cutoff)


def build_plan(path, protocol):
    config = protocol["code"]
    by_patient, seen = defaultdict(list), set()
    with path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            exam, patient = int(row["exam_id"]), row["patient_id"].strip()
            if exam <= 0 or exam in seen or not patient:
                raise ValueError("invalid source exam membership")
            seen.add(exam)
            by_patient[patient].append(row)
    groups = defaultdict(list)
    for patient in by_patient:
        split = assign(patient, config)
        if split not in config["exclude_historical_pr6_patients_from"] or not selected(patient):
            groups[split].append(patient)
    plan = defaultdict(dict)
    for split in SPLITS:
        patients = sorted(groups[split], key=lambda p: stable(config["assignment_seed"] + "-cap", p))
        for patient in patients[:config["patient_caps"][split]]:
            records = sorted(by_patient[patient], key=lambda r: stable(config["assignment_seed"] + "-ecg", r["exam_id"]))
            for row in records[:config["max_records_per_patient"]]:
                plan[Path(row["trace_file"]).with_suffix(".zip").name][int(row["exam_id"])] = (
                    patient, split, [label(row[column]) for column in protocol["endpoints"].values()], selected(patient),
                )
    return plan, len(seen), len(by_patient)


def write_json(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_bytes((json.dumps(value, sort_keys=True, indent=2) + "\n").encode())
    temporary.replace(path)


def process_archive(code, name, catalog, expected, plan, output, scratch):
    if digest(code / name) != expected:
        raise ValueError(f"{name}: archive differs from frozen CODE receipt")
    checkpoint = output / name.removesuffix(".zip")
    plan_hash = hashlib.sha256(json.dumps(plan, sort_keys=True).encode()).hexdigest()
    if checkpoint.is_dir():
        receipt = json.loads((checkpoint / "receipt.json").read_bytes())
        if receipt["archive_sha256"] != expected or receipt["plan_sha256"] != plan_hash:
            raise ValueError("materialization checkpoint input mismatch")
        for file, sha in receipt["artifacts"].items():
            if digest(checkpoint / file) != sha:
                raise ValueError("materialization checkpoint hash mismatch")
        return receipt
    staging = Path(tempfile.mkdtemp(prefix=checkpoint.name + ".writing.", dir=output))
    groups, rows, failures = defaultdict(list), [], Counter()
    h5path = verified_hdf5(code, name, catalog, scratch)
    try:
        with h5py.File(h5path, "r") as h5:
            ids = np.asarray(h5["exam_id"]).reshape(-1)
            traces = h5["tracings"]
            if traces.shape != (len(ids), 4096, 12) or not plan.keys() <= set(map(int, ids)):
                raise ValueError(f"{name}: HDF5 waveform/index mismatch")
            for index, exam in enumerate(ids):
                exam = int(exam)
                if exam not in plan:
                    continue
                patient, split, labels, exposed = plan[exam]
                try:
                    signal, duration = code_observed_window(traces[index])
                    wave = prepare_observed(signal, 400)
                except ValueError as exc:
                    failures[str(exc)] += 1
                    continue
                file = f"{split}-{duration}.npz"
                bucket = groups[file]
                fingerprint = hashlib.sha256(np.ascontiguousarray(signal, dtype="<f4").tobytes()).hexdigest()
                rows.append({"exam": exam, "patient": patient, "split": split, "labels": labels,
                             "historical_pr6_patient": exposed, "duration": duration,
                             "observed_samples_400hz": len(signal), "waveform_sha256": fingerprint,
                             "file": file, "row": len(bucket)})
                bucket.append((wave, observed_descriptors(wave)))
    finally:
        h5path.unlink(missing_ok=True)
    for file, bucket in groups.items():
        wave, descriptors = zip(*bucket, strict=True)
        np.savez(staging / file, wave=np.stack(wave), descriptors=np.stack(descriptors))
    write_json(staging / "rows.json", rows)
    receipt = {"archive_sha256": expected, "plan_sha256": plan_hash, "planned_ecgs": len(plan),
               "waveform_exclusions": dict(failures),
               "admitted_ecgs": len(rows), "artifacts": {file.name: digest(file) for file in staging.iterdir()}}
    write_json(staging / "receipt.json", receipt)
    staging.rename(checkpoint)
    return receipt


def finalize(output, receipts, protocol, source_n, source_p):
    pairs, patients, excluded = defaultdict(list), defaultdict(set), Counter()
    for folder, receipt in receipts.items():
        excluded.update(receipt["waveform_exclusions"])
        for row in json.loads((output / folder / "rows.json").read_bytes()):
            patients[row["patient"]].add(row["split"])
            row["file"] = f"{folder}/{row['file']}"
            pairs[row["waveform_sha256"]].append(row)
    if any(len(splits) != 1 for splits in patients.values()):
        raise ValueError("CODE patient leaked across new partitions")
    eligible = []
    for group in pairs.values():
        if len({r["split"] for r in group}) > 1:
            excluded["exact_waveform_cross_split"] += len(group)
        else:
            eligible.append(min(group, key=lambda r: r["exam"]))
            excluded["exact_waveform_within_split"] += len(group) - 1
    summary = {}
    for split in SPLITS:
        items = sorted((r for r in eligible if r["split"] == split), key=lambda r: r["exam"])
        if not items or (split != "train" and any(r["historical_pr6_patient"] for r in items)):
            raise ValueError("missing split or reused PR6 patient in an evaluation partition")
        write_json(output / f"private_{split}.json", items)
        y = np.asarray([r["labels"] for r in items])
        summary[split] = {
            "ecgs": len(items), "patients": len({r["patient"] for r in items}),
            "historical_pr6_patients": len({r["patient"] for r in items if r["historical_pr6_patient"]}),
            "duration": dict(Counter(r["duration"] for r in items)),
            "endpoint_counts": {name: {str(v): int((y[:, i] == v).sum()) for v in (-1, 0, 1)}
                                for i, name in enumerate(protocol["endpoints"])},
            "private_manifest_sha256": digest(output / f"private_{split}.json"),
        }
    planned = sum(r["planned_ecgs"] for r in receipts.values())
    if planned != len(eligible) + sum(excluded.values()):
        raise ValueError("CODE development ECG denominator mismatch")
    result = {"scope": "WITHIN_CODE_DEVELOPMENT_NOT_INSTITUTIONAL_CONFIRMATION",
              "protocol_sha256": digest(PROTOCOL), "source_ecgs": source_n, "source_patients": source_p,
              "planned_ecgs": planned, "splits": summary, "exclusions": dict(excluded),
              "patient_overlap": 0, "cross_source_overlap": "NOT_CERTIFIED",
              "signal_overlap_check": "exact float32 observed CODE waveform only; no cross-source patient equivalence claim"}
    write_json(output / "CODE_DEVELOPMENT_RECEIPT.json", result)
    print(json.dumps(result, sort_keys=True), flush=True)


def run(code, output, scratch):
    protocol = json.loads(PROTOCOL.read_bytes())
    metadata, transport = code / "exams.csv", code / "range_all_receipt.json"
    if (digest(metadata) != protocol["code"]["metadata_sha256"]
            or digest(transport) != protocol["code"]["archive_receipt_sha256"]):
        raise ValueError("CODE input receipt differs from registered study")
    plan, source_n, source_p = build_plan(metadata, protocol)
    archives = {r["archive"]: r["sha256"] for r in json.loads(transport.read_bytes())["archives"]}
    catalog = json.loads((code / "record.json").read_bytes())
    if len(archives) != 18 or not plan.keys() <= archives.keys():
        raise ValueError("CODE archive plan is incomplete")
    output.mkdir(mode=0o700, exist_ok=True)
    receipts = {}
    for name, sha in sorted(archives.items()):
        receipt = process_archive(code, name, catalog, sha, plan[name], output, scratch)
        receipts[name.removesuffix(".zip")] = receipt
        print(json.dumps({"archive": name, "admitted_ecgs": receipt["admitted_ecgs"]}), flush=True)
    finalize(output, receipts, protocol, source_n, source_p)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("code", "output", "scratch"):
        parser.add_argument(key, type=Path)
    args = parser.parse_args()
    run(args.code, args.output, args.scratch)
