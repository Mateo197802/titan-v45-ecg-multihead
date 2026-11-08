"""Independently reproduce patient-component bootstrap intervals for binary metrics."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def binary_intervals(truth, predicted, clusters, seed, replicates):
    truth = np.asarray(truth, dtype=np.int8)
    predicted = np.asarray(predicted, dtype=np.int8)
    unique = sorted(set(clusters))
    if not len(truth) or len(truth) != len(predicted) or len(truth) != len(clusters) or not unique:
        raise ValueError("invalid bootstrap population")
    cluster_number = {item: number for number, item in enumerate(unique)}
    indices = np.asarray([cluster_number[item] for item in clusters], dtype=np.int32)
    masks = {"tp": (truth == 1) & (predicted == 1), "tn": (truth == 0) & (predicted == 0),
             "fp": (truth == 0) & (predicted == 1), "fn": (truth == 1) & (predicted == 0)}
    rng = np.random.Generator(np.random.PCG64(seed))
    samples = {name: [] for name in ("accuracy", "sensitivity", "specificity", "precision", "npv", "f1")}
    for _ in range(replicates):
        selected = rng.integers(0, len(unique), size=len(unique))
        weights = np.bincount(selected, minlength=len(unique))[indices]
        count = {name: int(weights[mask].sum()) for name, mask in masks.items()}
        tp, tn, fp, fn = (count[name] for name in ("tp", "tn", "fp", "fn"))
        for name, numerator, denominator in (
            ("accuracy", tp + tn, tp + tn + fp + fn), ("sensitivity", tp, tp + fn),
            ("specificity", tn, tn + fp), ("precision", tp, tp + fp), ("npv", tn, tn + fn),
        ):
            if denominator:
                samples[name].append(numerator / denominator)
        denominator = 2 * tp + fp + fn
        samples["f1"].append(2 * tp / denominator if denominator else 0.0)
    return {name: {"low": float(np.quantile(values, 0.025)) if values else None,
                   "high": float(np.quantile(values, 0.975)) if values else None,
                   "valid_replicates": len(values), "invalid_replicates": replicates - len(values)}
            for name, values in samples.items()}


def _compare(actual, expected):
    for metric, result in actual.items():
        target = expected.get(metric)
        if target is None:
            if result["valid_replicates"]:
                raise ValueError(f"missing bootstrap interval: {metric}")
            continue
        for key, value in result.items():
            other = target[key]
            if value is None or other is None:
                if value != other:
                    raise ValueError(f"bootstrap mismatch: {metric} {key}")
            elif not math.isclose(value, other, abs_tol=1e-12, rel_tol=1e-12):
                raise ValueError(f"bootstrap mismatch: {metric} {key}")


def verify(metadata, ledger, duplicate_index, aggregate, protocol):
    references, patients = {}, {}
    with Path(metadata).open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            record = row["ECG_ID"]
            if record in references:
                raise ValueError("duplicate metadata record")
            references[record] = {int(item.split("+")[0]) for item in row["AHA_Code"].split(";")}
            patients[record] = row["Patient_ID"].strip()
    records = {}
    with Path(ledger).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row["record_id"] in records:
                raise ValueError("duplicate ledger record")
            records[row["record_id"]] = row
    by_signal = defaultdict(list)
    seen = set()
    with Path(duplicate_index).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            record = row["ecg_id"]
            if record in seen or record not in patients or row["patient_id"] != patients[record]:
                raise ValueError("duplicate index or patient mismatch")
            seen.add(record)
            by_signal[row["signal_sha256_canonical_f64"]].append(record)
    if (seen != references.keys() or records.keys() != references.keys()
            or len(records) != protocol["expected_source_records"]):
        raise ValueError("metadata, index and ledger populations differ")
    if any(len({patients[record] for record in group}) > 1 for group in by_signal.values()):
        raise ValueError("cross-patient signal group requires general component algorithm")
    checked = {}
    for index, endpoint in enumerate(protocol["endpoints"]):
        profile, name, codes = endpoint["profile"], endpoint["name"], set(endpoint["codes"])
        excluded = set()
        for group in by_signal.values():
            if len(group) > 1 and len({bool(codes & references[record]) for record in group}) > 1:
                excluded.update(group)
        rows = [(record, int(bool(codes & labels)), int(name in records[record]["profiles"][profile]["labels"]))
                for record, labels in references.items() if records[record]["status"] == "scored"]
        target = aggregate["endpoints"][f"{profile}:{name}"]
        for selection, target_ci in ((rows, target["cluster_bootstrap_ci95"]),
                                     ([row for row in rows if row[0] not in excluded],
                                      target["discordant_exact_duplicate_sensitivity"]["cluster_bootstrap_ci95"])):
            if not selection:
                if target_ci is not None:
                    raise ValueError("empty sensitivity analysis has an interval")
                continue
            ids, truth, predicted = zip(*selection, strict=True)
            intervals = binary_intervals(truth, predicted, [patients[record] for record in ids],
                                         protocol["bootstrap"]["seed"] + index,
                                         protocol["bootstrap"]["replicates"])
            _compare(intervals, target_ci)
        checked[f"{profile}:{name}"] = {"binary_metrics": 6, "primary_and_sensitivity": True}
    return {"schema": "TITAN_V45_SPH_INDEPENDENT_BINARY_BOOTSTRAP_V1", "endpoints": checked,
            "individual_records_exported": False, "script_sha256": sha256(__file__)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("metadata", "ledger", "duplicate-index", "aggregate", "protocol", "output"):
        parser.add_argument(f"--{name}", required=True, type=Path)
    args = parser.parse_args()
    report = verify(args.metadata, args.ledger, args.duplicate_index,
                    json.loads(args.aggregate.read_text()), json.loads(args.protocol.read_text()))
    report["inputs"] = {name: sha256(getattr(args, name)) for name in
                        ("metadata", "ledger", "duplicate_index", "aggregate", "protocol")}
    with args.output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")


if __name__ == "__main__":
    main()
