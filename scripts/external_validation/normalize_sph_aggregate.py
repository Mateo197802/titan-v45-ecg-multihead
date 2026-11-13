"""Add protocol metric aliases to a sealed aggregate without changing its inputs."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path


def normalize_metrics(metrics):
    if metrics is None:
        return None
    result = copy.deepcopy(metrics)
    tn, fp, fn, tp = (result[key] for key in ("tn", "fp", "fn", "tp"))
    if any(not isinstance(value, int) or value < 0 for value in (tn, fp, fn, tp)):
        raise ValueError("confusion counts must be nonnegative integers")
    sensitivity = tp / (tp + fn) if tp + fn else None
    recall = result["recall"]
    if (sensitivity is None) != (recall is None) or (
        sensitivity is not None and not math.isclose(sensitivity, recall, rel_tol=1e-12, abs_tol=1e-12)
    ):
        raise ValueError("recall does not match sensitivity from confusion counts")
    result["sensitivity"] = sensitivity
    result["npv"] = tn / (tn + fn) if tn + fn else None
    if result["npv"] is None:
        result.setdefault("undefined", {})["npv"] = "zero_denominator"
    return result


def normalize_report(report, input_sha256):
    if report.get("schema") != "TITAN_V45_SPH_ENDPOINT_RESULTS_V1":
        raise ValueError("expected SPH aggregate schema")
    result = copy.deepcopy(report)
    for endpoint in result["endpoints"].values():
        endpoint["metrics"] = normalize_metrics(endpoint["metrics"])
        sensitivity = endpoint["discordant_exact_duplicate_sensitivity"]
        sensitivity["metrics"] = normalize_metrics(sensitivity["metrics"])
    result["aggregate_normalization"] = {
        "input_sha256": input_sha256,
        "operations": ["sensitivity aliases recall", "npv is tn/(tn+fn)"],
        "bootstrap_intervals": "unchanged from frozen aggregate",
        "individual_predictions_or_reference_labels_read": False,
    }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    raw = args.input.read_bytes()
    report = normalize_report(json.loads(raw), hashlib.sha256(raw).hexdigest())
    with args.output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, indent=2, allow_nan=False)
        handle.write("\n")


if __name__ == "__main__":
    main()
