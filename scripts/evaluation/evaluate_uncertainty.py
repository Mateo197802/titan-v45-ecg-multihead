from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize MC-Dropout probability samples.")
    parser.add_argument("--samples", type=Path, required=True, help="NPY shaped [passes, records, classes].")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    samples = np.load(args.samples)
    if samples.ndim != 3 or samples.shape[0] < 2:
        raise ValueError("samples must have shape [passes>=2, records, classes]")
    clipped = np.clip(samples, 1e-12, 1.0)
    mean = samples.mean(axis=0)
    predictive_entropy = -(np.clip(mean, 1e-12, 1.0) * np.log(np.clip(mean, 1e-12, 1.0))).sum(axis=-1)
    expected_entropy = -(clipped * np.log(clipped)).sum(axis=-1).mean(axis=0)
    payload = {
        "records": int(samples.shape[1]),
        "passes": int(samples.shape[0]),
        "mean_predictive_entropy": float(predictive_entropy.mean()),
        "mean_mutual_information": float(np.maximum(predictive_entropy - expected_entropy, 0.0).mean()),
        "quarantine_policy": "entropy and mutual-information thresholds",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
