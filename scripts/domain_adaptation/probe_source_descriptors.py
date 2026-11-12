"""Probe descriptor source separability on development ECG of equal duration."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit
from train_duration_aware import digest, read_bank, read_extra, write_json

from titan_v45.evaluation.revision_report import binary_metrics


def source_inputs(code, extra, split):
    groups = (read_bank(code, split, "per_lead_zscore")[1250],
              read_extra(extra, "chapman_shaoxing", split, "per_lead_zscore")[1250])
    descriptors = np.concatenate([group[1] for group in groups]).astype(np.float64)
    truth = np.concatenate([np.full(len(group[1]), label) for label, group in enumerate(groups)])
    weights = np.concatenate([group[3] / (2 * group[3].sum()) for group in groups]).astype(np.float64)
    return descriptors, truth, weights, [len(group[1]) for group in groups]


def run(code, extra, output):
    train, y, w, train_n = source_inputs(code, extra, "train")
    val, reference, _, val_n = source_inputs(code, extra, "validation")
    center = np.average(train, axis=0, weights=w)
    scale = np.sqrt(np.average((train - center) ** 2, axis=0, weights=w)).clip(1e-8)
    fit = np.column_stack([np.ones(len(train)), (train - center) / scale])
    l2 = .01

    def objective(beta):
        z = fit @ beta
        loss = np.dot(w, np.logaddexp(0, z) - y * z) + l2 * np.dot(beta[1:], beta[1:]) / 2
        derivative = fit.T @ (w * (expit(z) - y))
        derivative[1:] += l2 * beta[1:]
        return loss, derivative

    fit_result = minimize(objective, np.zeros(fit.shape[1]), jac=True, method="L-BFGS-B")
    if not fit_result.success:
        raise RuntimeError("development source probe failed to converge")
    scores = expit(np.column_stack([np.ones(len(val)), (val - center) / scale]) @ fit_result.x)
    result = binary_metrics(reference, scores >= .5, scores)
    write_json(output, {"scope": "SOURCE_RECOGNITION_ONLY_NOT_DIAGNOSTIC", "positive_source": "chapman_shaoxing",
                        "negative_source": "code15", "ecg_duration_seconds": 10, "l2": l2,
                        "training_ecgs": train_n, "validation_ecgs": val_n,
                        "diagnostic_labels_used": False, "test_opened": False,
                        "balanced_accuracy": (result["recall"] + result["specificity"]) / 2,
                        "metrics": result, "code_bank_receipt_sha256": digest(code / "CODE_DEVELOPMENT_RECEIPT.json"),
                        "additional_source_receipt_sha256": digest(extra / "ADDITIONAL_SOURCE_RECEIPT.json"),
                        "probe_scope": "7 descriptors; does not measure the trained specialist's reliance on them"})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("code", "extra", "output"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    run(args.code, args.extra, args.output)
