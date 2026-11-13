"""Run the frozen evaluator with consistent ECE binning and an extra receipt."""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
import sys
from pathlib import Path

import numpy as np


def consistent_ece(truth, scores, weights, bins):
    truth = np.asarray(truth, dtype=np.float64)
    scores = np.asarray(scores, dtype=np.float64)
    weights = np.asarray(weights, dtype=np.int64)
    total = weights.sum()
    if not total:
        return None
    edges = np.linspace(0.0, 1.0, bins + 1)
    index = np.minimum(np.searchsorted(edges, scores, side="right") - 1, bins - 1)
    ece = 0.0
    for bin_number in range(bins):
        selected_weights = weights * (index == bin_number)
        count = selected_weights.sum()
        if count:
            ece += count / total * abs(np.dot(selected_weights, scores - truth) / count)
    return float(ece)


def corrected_metric_values(original, truth, predicted, scores, weights, ece_bins):
    values = original(truth, predicted, scores, weights, ece_bins)
    values["ece"] = consistent_ece(truth, scores, weights, ece_bins)
    return values


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__, add_help=False)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--receipt-output", required=True, type=Path)
    parser.add_argument("--correction-receipt", required=True, type=Path)
    args, remaining = parser.parse_known_args()
    repo = args.repo.resolve()
    if args.correction_receipt.resolve().is_relative_to(repo):
        raise ValueError("correction receipt must be staged outside the Git checkout")
    sys.path.insert(0, str(repo / "src"))
    import titan_v45.evaluation.sph_report as sph_report

    original = sph_report._metric_values

    def corrected(truth, predicted, scores, weights, ece_bins):
        return corrected_metric_values(original, truth, predicted, scores, weights, ece_bins)

    sph_report._metric_values = corrected
    evaluator = repo / "scripts/external_validation/evaluate_sph_ledger.py"
    sys.argv = [str(evaluator), "--repo", str(repo), "--output", str(args.output),
                "--receipt-output", str(args.receipt_output), *remaining]
    runpy.run_path(str(evaluator), run_name="__main__")
    receipt = {
        "schema": "TITAN_V45_SPH_ECE_CORRECTION_RECEIPT_V1",
        "correction": "bootstrap ECE bins use the frozen point-estimate searchsorted edges",
        "wrapper_sha256": sha256(__file__),
        "frozen_evaluator_sha256": sha256(evaluator),
        "aggregate_sha256": sha256(args.output),
        "frozen_evaluator_receipt_sha256": sha256(args.receipt_output),
        "other_bootstrap_metrics_modified": False,
    }
    with args.correction_receipt.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(receipt, handle, indent=2)
        handle.write("\n")


if __name__ == "__main__":
    main()
