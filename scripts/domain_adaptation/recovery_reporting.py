"""Reduce authorized private evidence to a fixed, aggregate-only delivery."""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
from pathlib import Path
from statistics import mean, stdev

import numpy as np
from recovery_calibration import bm, candidate_probs, csv_write, load_score
from recovery_inputs import RECOVERY, ROOT, config
from recovery_selection import checked_fits
from train_duration_aware import digest, write_json

TABLES = ("CLASSWISE_FAILURE_DIAGNOSIS.csv", "CLASSWISE_FALSE_POSITIVE_FALSE_NEGATIVE_AUDIT.csv",
          "THRESHOLD_SENSITIVITY_PRECISION_FRONTIERS.csv", "CALIBRATION_ABLATIONS.csv",
          "DOMAIN_GENERALIZATION_MATRIX.csv", "MODEL_PROMOTION_GATES.json")
FIT_FIELDS = ("mode", "seed", "best_epoch", "validation_macro_ap", "validation_guard_ap", "validation_f1_at_0_5",
              "trainable_at_best", "checkpoint_sha256", "parent_sha256", "curves_sha256", "slurm_job", "code_commit")
JOB_FIELDS = ("JobIDRaw", "State", "ExitCode", "ElapsedRaw", "AllocTRES", "Start", "End")


def source_audit(extra):
    receipt_path = extra / "ADDITIONAL_SOURCE_RECEIPT.json"
    cfg = config()
    if digest(receipt_path) != cfg["other_bank_sha256"]:
        raise ValueError("source receipt changed")
    receipt = json.loads(receipt_path.read_bytes())
    rows = {}
    for source, split in (("chapman_shaoxing", "train"), ("chapman_shaoxing", "validation"), ("cpsc2018", "train")):
        path = extra / f"private_{source}_{split}.json"
        check = receipt["sources"][f"{source}/{split}"]
        if digest(path) != check["private_manifest_sha256"]:
            raise ValueError("source manifest changed")
        rows[source, split] = json.loads(path.read_bytes())
        if len(rows[source, split]) != check["ecgs"]:
            raise ValueError("source manifest denominator changed")
    tr, va = (rows["chapman_shaoxing", split] for split in ("train", "validation"))
    overlap = {f"{k}_matches": len({r[k] for r in tr} & {r[k] for r in va})
               for k in ("group", "identity", "waveform_sha256")}
    if any(overlap.values()):
        raise ValueError("Chapman source split overlap")
    return {"chapman_train_validation_overlap_counts": overlap, "chapman_group_is_provider_proxy": True,
            "cpsc_patient_count": None, "cpsc_masked_endpoints": ["SB", "STACH"],
            "cross_source_independence": "NOT_CERTIFIED",
            "counts": {key: {"ecgs": row["ecgs"], "groups": row["patients"], "references": row["endpoints"]}
                       for key, row in receipt["sources"].items()}}


def accounting(jobs):
    if not jobs or any(not j.isdecimal() for j in jobs):
        raise ValueError("explicit numeric SLURM jobs required")
    values = subprocess.check_output(["sacct", "-X", "-n", "-P", "-S", "2026-11-12", "-j", ",".join(jobs),
                                     "--format", ",".join(JOB_FIELDS)], text=True).splitlines()
    rows = {r["JobIDRaw"]: r for r in (dict(zip(JOB_FIELDS, line.split("|"), strict=True)) for line in values if line)}
    if set(rows) != set(jobs):
        raise ValueError("SLURM did not return every requested job")
    return [rows[job] for job in jobs]


def fit_metrics(fits, results, diagnostics):
    cohorts = {key: load_score(diagnostics, key) for key in ("validation", "chapman", "cpsc")}
    for fit in results:
        mode, seed = fit["mode"], fit["seed"]
        folder = fits / f"{mode}-{seed}"
        for scope, data in cohorts.items():
            if scope == "cpsc" and "cpsc" in fit["training_sources"]:
                continue
            p = candidate_probs(folder, scope, data)
            for j, endpoint in enumerate(config()["endpoints"]):
                ok = data["labels"][:, j] >= 0
                if not np.any(ok):
                    continue
                # These are fixed, uncalibrated operating points for screening audit only.
                r = bm(data["labels"][ok, j], p[ok, j], .5)
                yield {"mode": mode, "seed": seed, "scope": scope, "endpoint": endpoint, "threshold": .5,
                       **{k: r[k] for k in ("positive_support", "negative_support", "tp", "tn", "fp", "fn",
                                             "recall", "precision", "specificity", "f1", "auroc", "average_precision")}}


def run(previous, diagnostics, fits, calibration, output, jobs, final=None, selected_scores=None):
    cfg = config()
    rows = checked_fits(fits, check_bytes=True)
    result = json.loads(final.read_bytes()) if final else None
    if result and result["protocol_sha256"] != digest(RECOVERY):
        raise ValueError("final selection protocol changed")
    output.mkdir(mode=0o700, exist_ok=False)
    names = []

    def add(name):
        names.append(name)
        return output / name

    for name in TABLES:
        add(name).write_bytes((calibration / name).read_bytes())
    add("DEVELOPMENT_SCORING_RECEIPT.json").write_bytes((diagnostics / "DEVELOPMENT_SCORING_RECEIPT.json").read_bytes())
    write_json(add("SOURCE_SPLIT_VERIFICATION.json"), source_audit(previous / "additional-sources-v2"))
    ledger = accounting(jobs)
    csv_write(add("SLURM_EXECUTION_LEDGER.csv"), ledger)
    if rows:
        csv_write(add("FINETUNING_EXPERIMENTS.csv"), [
            {**{k: r[k] for k in FIT_FIELDS}, **r["variant"], "status": "COMPLETED"} for r in rows])
        csv_write(add("FIT_CLASSWISE_ERROR_AUDIT.csv"), fit_metrics(fits, rows, diagnostics))
        csv_write(add("FINETUNING_LEARNING_CURVES.csv"), [
            {"mode": r["mode"], "seed": r["seed"], **curve}
            for r in rows for curve in read_csv(fits / f"{r['mode']}-{r['seed']}" / "FINETUNING_LEARNING_CURVES.csv")])
        add("EXPERIMENT_CHECKPOINT_SHA256SUMS.txt").write_text(
            "".join(f"{r['checkpoint_sha256']}  {r['mode']}-{r['seed']}/best.pt\n" for r in rows), encoding="ascii")
        modes = sorted({r["mode"] for r in rows})
        csv_write(add("TRAINING_SEEDS_AND_VARIANCE.csv"), [
            {"mode": mode, "n_seeds": len(aps), "mean_validation_macro_ap": mean(aps),
             "sample_sd_validation_macro_ap": stdev(aps) if len(aps) > 1 else None,
             "min_validation_macro_ap": min(aps), "max_validation_macro_ap": max(aps)}
            for mode in modes if (aps := [r["validation_macro_ap"] for r in rows if r["mode"] == mode])])
    failure_rows = []
    for path in sorted(fits.glob("*/FAILED_FIT_RECEIPT.json")):
        failure_rows.append(json.loads(path.read_bytes()))
    write_json(add("FIT_FAILURES.json"), failure_rows)
    if result:
        add("FINAL_SELECTION_RECEIPT.json").write_bytes(final.read_bytes())
    if selected_scores:
        add("CANDIDATE_SCORING_RECEIPT.json").write_bytes(
            (selected_scores / "MODEL_RECOVERY_FIT_RECEIPT.json").read_bytes())
    gpu_sec = sum(int(r["ElapsedRaw"]) for r in ledger if "gres/gpu" in r["AllocTRES"])
    if gpu_sec > cfg["training"]["max_gpu_allocation_hours"] * 3600:
        raise ValueError("GPU budget was exceeded")
    write_json(output / "PUBLIC_VERIFICATION_RECEIPT.json", {
        "protocol_sha256": digest(RECOVERY), "old_test_opened": False, "independent_confirmation": "NOT_EVALUATED",
        "checked_fits": len(rows), "failed_fits": len(failure_rows), "gpu_allocation_seconds": gpu_sec,
        "code_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "sha256": {name: digest(output / name) for name in sorted(names)}})


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("previous", "diagnostics", "fits", "calibration", "output"):
        parser.add_argument(key, type=Path)
    parser.add_argument("jobs", help="comma-separated numeric SLURM jobs")
    parser.add_argument("--final", type=Path)
    parser.add_argument("--selected-scores", type=Path)
    args = vars(parser.parse_args())
    args["jobs"] = args["jobs"].split(",")
    run(**args)
