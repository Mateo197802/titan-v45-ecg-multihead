"""Seal fit selection from validation metrics before candidate calibration."""
from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path

import numpy as np
import torch
from recovery_inputs import RECOVERY, SOURCES, config, parent_model
from recovery_training import RecoveryNet, aux_data, get_code, write_scores
from train_duration_aware import digest, write_json


def checked_fits(fits, check_bytes=False):
    cfg = config()
    results = []
    for path in sorted(fits.glob("*/MODEL_RECOVERY_FIT_RECEIPT.json")):
        row = json.loads(path.read_bytes())
        mode, seed = row["mode"], row["seed"]
        if (path.parent.name != f"{mode}-{seed}" or row["protocol_sha256"] != digest(RECOVERY)
                or row["old_test_opened"] or row["calibration_opened"]
                or row["parent_sha256"] != cfg["parent_checkpoints"][str(seed)]
                or row["variant"] != cfg["training"]["screen"][mode]):
            raise ValueError("invalid fit receipt")
        if check_bytes:
            checks = {"best.pt": row["checkpoint_sha256"], "FINETUNING_LEARNING_CURVES.csv": row["curves_sha256"],
                      **row["private_score_sha256"]}
            if any(digest(path.parent / name) != expected for name, expected in checks.items()):
                raise ValueError("fit artifact custody failure")
        results.append(row)
    return results


def rank(rows):
    return sorted(rows, key=lambda r: (-r["validation_macro_ap"], -r["validation_guard_ap"], r["mode"]))


def full_decision(rows, incumbent):
    cfg = config()
    partial = rank([r for r in rows if r["seed"] == cfg["training"]["screen_seed"] and r["mode"] != "full"])
    if not partial:
        raise ValueError("no successful partial screen")
    gain = partial[0]["validation_macro_ap"] - incumbent["code_validation"]["A"]["macro_raw_auprc"]
    return {"allow_full": not incumbent["incumbent_calibration_all_guards_feasible"] or gain < .02,
            "incumbent_calibration_feasible": incumbent["incumbent_calibration_all_guards_feasible"],
            "best_partial": partial[0]["mode"], "best_partial_gain": gain, "repeat_modes": []}


def finalists(rows):
    cfg = config()
    screen = rank([r for r in rows if r["seed"] == cfg["training"]["screen_seed"]])
    groups = ([r for r in screen if r["mode"] not in ("chapman", "cpsc", "mimic")],
              [r for r in screen if r["mode"] in ("chapman", "cpsc", "mimic")])
    return [group[0]["mode"] for group in groups if group]


def select(phase, fits, baseline, output, prior=None):
    cfg = config()
    rows = checked_fits(fits, check_bytes=phase == "final")
    incumbent = json.loads(baseline.read_bytes())
    if incumbent["protocol_sha256"] != digest(RECOVERY):
        raise ValueError("incumbent receipt protocol changed")
    result = full_decision(rows, incumbent)
    if phase != "full":
        result["repeat_modes"] = finalists(rows)
    if phase == "final":
        frozen = json.loads(prior.read_bytes())
        if frozen["protocol_sha256"] != digest(RECOVERY) or frozen["repeat_modes"] != result["repeat_modes"]:
            raise ValueError("finalist list changed")
        families = []
        for mode in result["repeat_modes"]:
            family = sorted([r for r in rows if r["mode"] == mode],
                            key=lambda r: (r["validation_macro_ap"], r["seed"]))
            if {r["seed"] for r in family} != set(cfg["training"]["seeds"]):
                continue
            mid = family[len(family) // 2]
            families.append({"mode": mode, "mean_validation_macro_ap": float(np.mean(
                [r["validation_macro_ap"] for r in family])), "representative_seed": mid["seed"],
                "representative_sha256": mid["checkpoint_sha256"]})
        families.sort(key=lambda r: (-r["mean_validation_macro_ap"], r["mode"]))
        result["families"] = families
        result["selected"] = families[0] if families else None
        result["repeat_gate_sha256"] = digest(prior)
    result.update({"phase": phase, "protocol_sha256": digest(RECOVERY), "slurm_job": os.getenv("SLURM_JOB_ID"),
                   "baseline_receipt_sha256": digest(baseline), "successful_fits": len(rows)})
    write_json(output, result)
    print(json.dumps(result, sort_keys=True), flush=True)


def score(previous, diagnostics, fits, final, output):
    frozen = json.loads(final.read_bytes())
    selected = frozen["selected"]
    if frozen["phase"] != "final" or frozen["protocol_sha256"] != digest(RECOVERY) or not selected:
        raise ValueError("three-seed selection has not been sealed")
    mode, seed = selected["mode"], selected["representative_seed"]
    source = fits / f"{mode}-{seed}"
    weight = source / "best.pt"
    receipt = json.loads((source / "MODEL_RECOVERY_FIT_RECEIPT.json").read_bytes())
    if digest(weight) != selected["representative_sha256"] or digest(weight) != receipt["checkpoint_sha256"]:
        raise ValueError("selected checkpoint changed")
    variant = receipt["variant"]
    model = RecoveryNet(parent_model(previous, seed), variant["head"])
    saved = torch.load(weight, map_location="cpu", weights_only=True)
    model.load_state_dict(saved["state_dict"], strict=True)
    model.cuda()
    output.mkdir(mode=0o700, exist_ok=False)
    for scope in ("validation", *SOURCES):
        file = source / f"private_{scope}.npz"
        if scope == "cpsc" and "cpsc" in receipt["training_sources"]:
            continue
        if digest(file) != receipt["private_score_sha256"][file.name]:
            raise ValueError("frozen validation or source scores changed")
        shutil.copyfile(file, output / file.name)
    path = output / "private_calibration.npz"
    rr = aux_data(diagnostics, "calibration")[0] if mode == "specialist" else None
    write_scores(path, model, get_code(previous, "calibration", variant["normalization"]), rr)
    receipt["private_score_sha256"][path.name] = digest(path)
    receipt.update({"candidate_calibration_scored_after_selection": True, "selection_sha256": digest(final),
                    "candidate_calibration_slurm_job": os.getenv("SLURM_JOB_ID")})
    write_json(output / "MODEL_RECOVERY_FIT_RECEIPT.json", receipt)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    run_select = sub.add_parser("select")
    run_select.add_argument("phase", choices=("full", "repeats", "final"))
    for key in ("fits", "baseline", "output"):
        run_select.add_argument(key, type=Path)
    run_select.add_argument("--prior", type=Path)
    run_score = sub.add_parser("score")
    for key in ("previous", "diagnostics", "fits", "final", "output"):
        run_score.add_argument(key, type=Path)
    args = vars(parser.parse_args())
    command = args.pop("command")
    (select if command == "select" else score)(**args)
