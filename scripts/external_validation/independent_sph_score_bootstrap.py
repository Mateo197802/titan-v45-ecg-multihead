"""Recompute frozen score-metric bootstrap intervals from private SPH records."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

METRICS = ("auroc", "average_precision", "brier_score", "ece")


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def score_intervals(truth, scores, clusters, *, seed, replicates, bins):
    truth = np.asarray(truth)
    scores = np.asarray(scores, dtype=np.float64)
    if (truth.ndim != 1 or scores.shape != truth.shape or len(clusters) != len(truth)
            or not len(truth) or not np.isin(truth, [0, 1]).all()
            or not np.isfinite(scores).all() or np.any((scores < 0) | (scores > 1))
            or bins < 1 or replicates < 1):
        raise ValueError("invalid score bootstrap population or configuration")
    unique = sorted(set(clusters))
    lookup = {cluster: index for index, cluster in enumerate(unique)}
    cluster_index = np.asarray([lookup[cluster] for cluster in clusters], dtype=np.int32)
    order = np.argsort(scores, kind="stable")
    sorted_scores, sorted_truth = scores[order], truth[order].astype(np.int8)
    starts = np.r_[0, np.flatnonzero(np.diff(sorted_scores)) + 1]
    bin_index = np.minimum(np.searchsorted(np.linspace(0.0, 1.0, bins + 1), scores,
                                           side="right") - 1, bins - 1)
    residual = scores - truth
    rng = np.random.Generator(np.random.PCG64(seed))
    samples = {metric: [] for metric in METRICS}
    for _ in range(replicates):
        draw = rng.integers(0, len(unique), size=len(unique))
        weights = np.bincount(draw, minlength=len(unique))[cluster_index]
        total = int(weights.sum())
        samples["brier_score"].append(float(np.dot(weights, residual ** 2) / total))
        by_bin = np.bincount(bin_index, weights=weights * residual, minlength=bins)
        samples["ece"].append(float(np.abs(by_bin).sum() / total))
        sorted_weights = weights[order]
        positives = np.add.reduceat(sorted_weights * sorted_truth, starts)
        negatives = np.add.reduceat(sorted_weights * (1 - sorted_truth), starts)
        active = (positives + negatives) > 0
        positives, negatives = positives[active], negatives[active]
        pos_total, neg_total = int(positives.sum()), int(negatives.sum())
        if pos_total and neg_total:
            neg_below = np.cumsum(negatives) - negatives
            samples["auroc"].append(float(np.dot(positives, neg_below + negatives / 2)
                                          / (pos_total * neg_total)))
        if pos_total:
            cum_pos = np.cumsum(positives[::-1])
            cum_all = cum_pos + np.cumsum(negatives[::-1])
            samples["average_precision"].append(float(
                np.dot(positives[::-1] / pos_total, cum_pos / cum_all)))
    return {metric: {"low": float(np.quantile(values, 0.025)) if values else None,
                     "high": float(np.quantile(values, 0.975)) if values else None,
                     "valid_replicates": len(values), "invalid_replicates": replicates - len(values)}
            for metric, values in samples.items()}


def compare_intervals(actual, expected):
    for metric, result in actual.items():
        target = expected.get(metric)
        if target is None:
            if result["valid_replicates"]:
                raise ValueError(f"missing interval: {metric}")
            continue
        for key, value in result.items():
            other = target[key]
            if value is None or other is None:
                if value != other:
                    raise ValueError(f"interval mismatch: {metric} {key}")
            elif not math.isclose(value, other, rel_tol=1e-12, abs_tol=1e-12):
                raise ValueError(f"interval mismatch: {metric} {key}: {value} != {other}")


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
        raise ValueError("cross-patient duplicate requires general component algorithm")
    checked = {}
    for index, endpoint in enumerate(protocol["endpoints"]):
        profile, name, codes = endpoint["profile"], endpoint["name"], set(endpoint["codes"])
        excluded = set()
        for group in by_signal.values():
            if len(group) > 1 and len({bool(codes & references[record]) for record in group}) > 1:
                excluded.update(group)
        rows = [(record, int(bool(codes & labels)),
                 float(records[record]["profiles"][profile]["scores"][name]))
                for record, labels in references.items() if records[record]["status"] == "scored"]
        target = aggregate["endpoints"][f"{profile}:{name}"]
        for selection, target_ci in ((rows, target["cluster_bootstrap_ci95"]),
                                     ([row for row in rows if row[0] not in excluded],
                                      target["discordant_exact_duplicate_sensitivity"]["cluster_bootstrap_ci95"])):
            if not selection:
                if target_ci is not None:
                    raise ValueError("empty sensitivity analysis has an interval")
                continue
            ids, truth, scores = zip(*selection, strict=True)
            intervals = score_intervals(truth, scores, [patients[record] for record in ids],
                                        seed=protocol["bootstrap"]["seed"] + index,
                                        replicates=protocol["bootstrap"]["replicates"],
                                        bins=protocol["metrics"]["ece_bins"])
            compare_intervals(intervals, target_ci)
        checked[f"{profile}:{name}"] = {"score_metrics": 4, "primary_and_sensitivity": True}
    return {"schema": "TITAN_V45_SPH_INDEPENDENT_SCORE_BOOTSTRAP_V1", "endpoints": checked,
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
