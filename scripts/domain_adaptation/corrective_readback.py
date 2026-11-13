"""Recompute matched point estimates from private, hash-sealed predictions."""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
from pathlib import Path

import numpy as np
from audit_private_holdout import points
from corrective_audit import PROTOCOL, cfg
from recovery_calibration import transform
from recovery_inputs import config
from train_duration_aware import digest, write_json

METRICS = {"sensitivity": "recall", "specificity": "specificity", "ppv": "precision", "npv": "npv",
           "f1": "f1", "auroc": "auroc", "auprc": "average_precision", "brier": "brier_score", "ece": "ece"}


def recompute(y, raw, prob, cut):
    result = points(y.astype(int), prob, .5)
    called = raw.astype(np.float64) >= cut
    tn, fp, fn, tp = map(int, np.bincount(2 * y.astype(int) + called, minlength=4))
    result.update(tp=tp, tn=tn, fp=fp, fn=fn, sensitivity=tp / (tp + fn),
                  specificity=tn / (tn + fp), f1=2 * tp / (2 * tp + fn + fp),
                  ppv=tp / (tp + fp) if tp + fp else None, npv=tn / (tn + fn) if tn + fn else None)
    return result


def run(folder, output):
    receipt = json.loads((folder / "CORRECTIVE_DECISION.json").read_bytes())
    if receipt["protocol_sha256"] != digest(PROTOCOL) or receipt["test_opened"]:
        raise ValueError("invalid readback scope")
    for name, sha in receipt["public_sha256"].items():
        if digest(folder / name) != sha:
            raise ValueError("public readback hash mismatch")
    with (folder / "CORRECTIVE_METRICS.csv").open(newline="", encoding="utf-8") as stream:
        rows = {(r["scope"], r["arm"], r["endpoint"]): r for r in csv.DictReader(stream)}
    selected = json.loads((folder / "CORRECTIVE_SELECTION.json").read_bytes())["selected"]
    total, max_error = 0, 0.
    for scope in ("validation", "chapman", "cpsc"):
        name = f"private_{scope}.npz"
        file = folder / name
        if digest(file) != receipt["private_score_sha256"][name]:
            raise ValueError("private readback hash mismatch")
        with np.load(file, allow_pickle=False) as z:
            for j, endpoint in enumerate(cfg()["endpoints"]):
                y = z["labels"][:, j]
                valid = y >= 0
                if set(y[valid]) != {0, 1}:
                    continue
                for arm, key in (("A", "incumbent"), ("C", "candidate")):
                    raw = z[key][valid, j]
                    cut = (config()["incumbent_thresholds"] if arm == "A" else selected["policy"]["cuts"])[j]
                    p = raw if arm == "A" else transform(raw, selected["policy"]["maps"][j])
                    rebuilt = recompute(y[valid], raw, p, cut)
                    row = rows.pop((scope, arm, endpoint))
                    for metric, column in {**METRICS, **{k: k for k in ("tp", "tn", "fp", "fn")}}.items():
                        a, b = rebuilt[metric], float(row[column]) if row[column] else None
                        if (a is None) != (b is None) or (a is not None and not math.isclose(a, b, abs_tol=1e-7)):
                            raise ValueError(f"private readback disagrees: {scope}/{arm}/{endpoint}/{metric}")
                        max_error = max(max_error, abs(a - b) if a is not None else 0.)
                    total += 1
    if rows:
        raise ValueError("unmatched public readback rows")
    write_json(output, {"protocol_sha256": digest(PROTOCOL), "source_decision_sha256": digest(
        folder / "CORRECTIVE_DECISION.json"), "rows_verified": total, "max_absolute_error": max_error,
        "slurm_job": os.getenv("SLURM_JOB_ID"), "test_opened": False})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("output", type=Path)
    run(**vars(parser.parse_args()))
