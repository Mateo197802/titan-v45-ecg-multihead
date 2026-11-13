"""Independently recompute SPH point metrics without exporting individual rows."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def points(rows):
    counts = {"tp": 0, "tn": 0, "fp": 0, "fn": 0}
    groups = {}
    squared_error = 0.0
    for truth, predicted, score in rows:
        if truth not in (0, 1) or predicted not in (0, 1) or not 0 <= score <= 1:
            raise ValueError("invalid binary record or probability")
        counts[{(1, 1): "tp", (0, 0): "tn", (0, 1): "fp", (1, 0): "fn"}[(truth, predicted)]] += 1
        group = groups.setdefault(score, [0, 0])
        group[truth] += 1
        squared_error += (score - truth) ** 2
    positives = counts["tp"] + counts["fn"]
    negatives = counts["tn"] + counts["fp"]
    neg_below, favorable = 0, 0.0
    for score in sorted(groups):
        neg, pos = groups[score]
        favorable += pos * (neg_below + neg / 2)
        neg_below += neg
    cumulative_positive = cumulative_total = 0
    ap = 0.0
    for score in sorted(groups, reverse=True):
        neg, pos = groups[score]
        cumulative_positive += pos
        cumulative_total += neg + pos
        if positives:
            ap += (pos / positives) * (cumulative_positive / cumulative_total)
    return {**counts, "rows": len(rows),
            "auroc": favorable / (positives * negatives) if positives and negatives else None,
            "average_precision": ap if positives else None,
            "brier_score": squared_error / len(rows) if rows else None}


def verify(source, ledger, aggregate, protocol):
    with Path(source).open(encoding="utf-8-sig", newline="") as handle:
        references = {}
        for row in csv.DictReader(handle):
            record = row["ECG_ID"]
            if record in references:
                raise ValueError("duplicate metadata record")
            references[record] = {int(item.split("+")[0]) for item in row["AHA_Code"].split(";")}
    records = {}
    with Path(ledger).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row["record_id"] in records:
                raise ValueError("duplicate ledger record")
            records[row["record_id"]] = row
    if references.keys() != records.keys() or len(records) != protocol["expected_source_records"]:
        raise ValueError("metadata and ledger population mismatch")
    compared = {}
    for endpoint in protocol["endpoints"]:
        profile, name, codes = endpoint["profile"], endpoint["name"], set(endpoint["codes"])
        rows = []
        for record, codes_in_record in references.items():
            row = records[record]
            if row["status"] != "scored":
                continue
            output = row["profiles"][profile]
            rows.append((int(bool(codes & codes_in_record)), int(name in output["labels"]),
                         float(output["scores"][name])))
        expected = aggregate["endpoints"][f"{profile}:{name}"]["metrics"]
        result = points(rows)
        for key, value in result.items():
            target = expected[key]
            if value is None or target is None:
                if value != target:
                    raise ValueError(f"{profile}:{name} {key} undefined mismatch")
            elif not math.isclose(value, target, rel_tol=1e-10, abs_tol=1e-10):
                raise ValueError(f"{profile}:{name} {key} mismatch")
        compared[f"{profile}:{name}"] = {"records": len(rows), "checks_passed": len(result)}
    return {"schema": "TITAN_V45_SPH_INDEPENDENT_POINTS_V1", "endpoints": compared,
            "individual_records_exported": False,
            "inputs": {"metadata_sha256": sha256(source), "ledger_sha256": sha256(ledger)},
            "script_sha256": sha256(__file__)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "ledger", "aggregate", "protocol", "output"):
        parser.add_argument(f"--{name}", required=True, type=Path)
    args = parser.parse_args()
    result = verify(args.source, args.ledger, json.loads(args.aggregate.read_text()),
                    json.loads(args.protocol.read_text()))
    result["inputs"]["aggregate_sha256"] = sha256(args.aggregate)
    result["inputs"]["protocol_sha256"] = sha256(args.protocol)
    with args.output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")


if __name__ == "__main__":
    main()
