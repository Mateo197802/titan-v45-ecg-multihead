"""Recompute the paired CODE macro-F1 interval using patient confusion counts."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import numpy as np
from autonomous_worker import PROTOCOL
from corrective_audit import cfg
from recovery_calibration import load_score
from recovery_inputs import config
from train_duration_aware import digest, write_json


def interval(y, a, c, groups, cuts_a, cuts_c, replicates, seed):
    _, first, reverse = np.unique(groups, return_index=True, return_inverse=True)
    order = np.argsort(first)
    restore = np.argsort(order)
    group = restore[reverse]
    cells = np.zeros((len(order), 2, y.shape[1], 4), dtype=np.int64)
    for m, (p, cuts) in enumerate(((a, cuts_a), (c, cuts_c))):
        for j in range(y.shape[1]):
            valid = y[:, j] >= 0
            outcomes = 2 * y[valid, j].astype(int) + (p[valid, j].astype(float) >= cuts[j])
            np.add.at(cells[:, m, j], (group[valid], outcomes), 1)

    def delta(counts):
        tn, fp, fn, tp = np.moveaxis(counts, -1, 0)
        if np.any(tp + fn == 0) or np.any(tn + fp == 0):
            return None
        f1 = (2 * tp / (2 * tp + fp + fn)).mean(axis=-1)
        return float(f1[1] - f1[0])

    rng = np.random.default_rng(seed)
    draws = [delta(cells[rng.integers(len(order), size=len(order))].sum(axis=0)) for _ in range(replicates)]
    valid = [v for v in draws if v is not None]
    return delta(cells.sum(axis=0)), *np.quantile(valid, [.025, .975]).tolist(), len(valid)


def run(archive, root, output):
    final = json.loads((root / "final.json").read_bytes())
    winner = final["fits"][final["finalist"]]
    val = load_score(archive, "validation")
    file = root / "fits" / final["finalist"] / "private_scores.npz"
    if (digest(file) != winner["scores_sha256"] or final["historical_test_opened"]
            or final["state"]["protocol_sha256"] != digest(PROTOCOL)):
        raise ValueError("private interval inputs failed their seals")
    spec = cfg()["paired_bootstrap"]
    with np.load(file, allow_pickle=False) as z:
        point, lower, upper, valid = interval(
            val["labels"], val["p"], z["validation"], val["patients"], config()["incumbent_thresholds"],
            winner["policy"]["cuts"], spec["replicates"], spec["seed"])
    reported = next(r for r in final["intervals"]["validation"]
                    if (r["arm"], r["endpoint"], r["metric"]) == ("C-A", "macro", "f1"))
    error = max(abs(v - reported[k]) for v, k in zip((point, lower, upper), ("value", "ci_low", "ci_high"), strict=True))
    if error > 1e-12 or valid != reported["valid_replicates"]:
        raise ValueError("paired CI failed independent confusion-count recomputation")
    write_json(output, {"protocol_sha256": digest(PROTOCOL), "slurm_job": os.getenv("SLURM_JOB_ID"),
                        "valid_replicates": valid, "max_absolute_error": error, "test_opened": False,
                        "scope": "CODE_SELECTION_ONLY", "metric": "paired_macro_f1"})


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for arg in ("archive", "root", "output"):
        p.add_argument(arg, type=Path)
    run(**vars(p.parse_args()))
