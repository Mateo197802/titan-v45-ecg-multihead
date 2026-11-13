"""Independently audit private loop outputs and export aggregate-only evidence."""
from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
from pathlib import Path
from statistics import mean, stdev

import numpy as np
from autonomous_worker import PROTOCOL, SCOPES, read_fit, settings
from corrective_readback import recompute
from recovery_calibration import csv_write, load_score, transform
from recovery_inputs import audit_splits, config
from recovery_reporting import source_audit
from train_duration_aware import digest, write_json


def slurm(slots):
    ids = slots.read_text().split()
    if len(ids) != len(set(ids)) or any(not j.isdecimal() for j in ids):
        raise ValueError("invalid slot roster")
    keys = ("JobIDRaw", "State", "ExitCode", "ElapsedRaw", "AllocTRES")
    cmd = ["sacct", "-X", "-n", "-P", "-j", ",".join(ids), "--format", ",".join(keys)]
    rows = [dict(zip(keys, line.split("|"), strict=True)) for line in subprocess.check_output(
        cmd, text=True).splitlines() if line]
    if {r["JobIDRaw"] for r in rows} != set(ids) or any(r["State"] in {"RUNNING", "PENDING"} for r in rows):
        raise ValueError("slot accounting is incomplete")
    return rows


def audit_scores(root, archive, fits):
    data = {s: load_score(archive, s) for s in SCOPES}
    total, error = 0, 0.
    for name, fit in fits.items():
        if read_fit(root / "fits" / name) != fit:
            raise ValueError("verified fit differs from final state")
        with np.load(root / "fits" / name / "private_scores.npz", allow_pickle=False) as z:
            for row in fit["points"]:
                s, j = row["scope"], config()["endpoints"].index(row["endpoint"])
                y = data[s]["labels"][:, j]
                known = y >= 0
                raw = z[s][known, j]
                policy = fit["chapman_policy"] if s == "chapman" else fit["policy"]
                p = transform(raw, policy["maps"][j])
                rebuilt = recompute(y[known], raw, p, policy["cuts"][j])
                pairs = {"recall": "sensitivity", "precision": "ppv", "average_precision": "auprc",
                         "brier_score": "brier", **{k: k for k in ("tp", "tn", "fp", "fn", "f1", "ece")}}
                for col, key in pairs.items():
                    a, b = row[col], rebuilt[key]
                    if (a is None) != (b is None) or (a is not None and not math.isclose(a, b, abs_tol=1e-7)):
                        raise ValueError(f"point readback mismatch: {name}/{s}/{col}")
                    if a is not None:
                        error = max(error, abs(a - b))
                total += 1
    return {"rows": total, "max_absolute_error": error}


def run(previous, archive, root, slots, output):
    out = json.loads((root / "final.json").read_bytes())
    state, fits = out["state"], out["fits"]
    c = settings()
    if (state["protocol_sha256"] != digest(PROTOCOL) or len(state["cycles"]) > c["limits"]["cycles"]
            or len(state["attempts"]) > c["limits"]["fit_attempts"] or out["historical_test_opened"]):
        raise ValueError("invalid budget, protocol or access state")
    integrity = {"code": audit_splits(previous / "code-bank"), "sources": source_audit(previous / "additional-sources-v2")}
    if integrity != state["integrity"]:
        raise ValueError("split evidence changed")
    jobs = slurm(slots)
    by_job = {r["JobIDRaw"]: r for r in jobs}
    if any(r["job"] not in by_job for r in fits.values()):
        raise ValueError("fit missing from SLURM ledger")
    gpu_seconds = sum(int(r["ElapsedRaw"]) for r in jobs if "gres/gpu" in r["AllocTRES"])
    if gpu_seconds > c["limits"]["gpu_seconds"]:
        raise ValueError("SLURM allocation exceeded budget")
    readback = audit_scores(root, archive, fits)
    output.mkdir(mode=0o700, exist_ok=False)
    ledger = []
    for row in jobs:
        attempt = [a for a in state["attempts"] if a["job"] == row["JobIDRaw"]]
        ledger.append({**row, "attempts": len(attempt), "verified_fits": sum(r["job"] == row["JobIDRaw"]
                       for r in fits.values())})
    csv_write(output / "AUTONOMOUS_LOOP_EXECUTION_LEDGER.csv", ledger)
    write_json(output / "ITERATION_HYPOTHESES_AND_DECISIONS.json", {
        "protocol_sha256": digest(PROTOCOL), "cycles": state["cycles"], "attempts": state["attempts"],
        "hypotheses": c["hypothesis"], "split_audit": integrity, "readback": readback,
        "verified_fits": {k: {key: r[key] for key in ("job", "epoch", "history", "guards", "summary", "anchor_sha256",
                                                     "parent_sha256", "scores_sha256")} for k, r in fits.items()}})
    csv_write(output / "CLASSWISE_ERROR_EVOLUTION.csv", [
        {"fit": k, **point} for k, r in fits.items() for point in r["points"]])
    (output / "TRAINING_CHECKPOINT_SHA256SUMS.txt").write_text(
        "".join(f"{r['checkpoint_sha256']}  {k}/best.pt\n" for k, r in fits.items()), encoding="ascii")
    final = out["finalist"]
    write_json(output / "BEST_DEVELOPMENT_MODEL.json", {
        "finalist": final, "incumbent": state["incumbent"], "working": state["working"],
        "fit": fits.get(final), "predecessor_chain": ancestry(fits, final),
        "best_screen_f1": max(r["summary"]["f1"] for r in fits.values()),
        "best_screen_ap": max(r["summary"]["average_precision"] for r in fits.values())})
    variance = []
    for cycle in state["cycles"]:
        for family in cycle.get("family", []):
            f = [fits[k] for k in family["members"]]
            for r in f:
                variance.append({"cycle": cycle["number"], "endpoint": r["endpoint"], "arm": r["arm"],
                                 "seed": r["seed"], "f1": r["summary"]["f1"], "ap": r["summary"]["average_precision"],
                                 "mean_f1": mean(x["summary"]["f1"] for x in f),
                                 "sample_sd_f1": stdev(x["summary"]["f1"] for x in f),
                                 "all_class_guards": all(g["pass"] for g in r["guards"].values())})
    csv_write(output / "THREE_SEED_STABILITY.csv", variance)
    transfer = [r for s in ("chapman", "cpsc") for r in out["intervals"].get(s, [])]
    csv_write(output / "MULTISOURCE_GENERALIZATION_RESULTS.csv", transfer)
    csv_write(output / "FINAL_PERFORMANCE_COMPARISON.csv", out["intervals"]["validation"])
    (output / "REMAINING_TECHNICAL_BLOCKERS.md").write_text(
        "# Remaining technical blockers\n\n"
        f"- Stop: `{state['stop']}`. Completed cycles: {len(state['cycles'])}; verified fits: {len(fits)}.\n"
        "- Repeated CODE validation and exposed transfer banks were selection data. Their intervals are descriptive.\n"
        "- No independent authorized institution was scored. HEEDB was not accessed.\n"
        "- Chapman groups are provider proxies. CPSC cannot support patient-level inference or SB/STACH.\n"
        "- No clinically validated PR measurements were inferred. P4 and historical cascade are outside this loop.\n",
        encoding="ascii")
    entries = {p.name: digest(p) for p in output.iterdir()}
    write_json(output / "MODEL_PROMOTION_DECISION.json", {
        "protocol_sha256": digest(PROTOCOL), "stop": state["stop"], "cycles": len(state["cycles"]),
        "attempts": len(state["attempts"]), "verified_fits": len(fits), "allocated_gpu_seconds": gpu_seconds,
        "finalist": final, "independent_generalization": "NOT_EVALUATED", "promotion": "NOT_AUTHORIZED",
        "historical_test_opened": False, "selection_reuse": True, "audit_job": os.getenv("SLURM_JOB_ID"),
        "files": entries})


def ancestry(fits, final):
    by_hash = {r["checkpoint_sha256"]: name for name, r in fits.items()}
    chain = []
    while final in fits:
        if final in chain:
            raise ValueError("cyclic model ancestry")
        chain.append(final)
        final = by_hash.get(fits[final]["anchor_sha256"])
    return chain


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for arg in ("previous", "archive", "root", "slots", "output"):
        p.add_argument(arg, type=Path)
    run(**vars(p.parse_args()))
