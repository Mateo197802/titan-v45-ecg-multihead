"""Verify the public performance recovery evidence without restricted inputs."""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev

from verify_adaptation_delivery import assert_hash

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "docs/performance_recovery/MODEL_PERFORMANCE_RECOVERY_PROTOCOL.json"
HEX = re.compile(r"[0-9a-f]{64}\Z")
PRIVATE_FIELDS = {"patient", "patient_id", "exam", "exam_id", "record_id", "identity", "waveform", "labels", "prediction"}
PUBLIC_FILES = set("""
CLASSWISE_FAILURE_DIAGNOSIS.csv CLASSWISE_FALSE_POSITIVE_FALSE_NEGATIVE_AUDIT.csv
THRESHOLD_SENSITIVITY_PRECISION_FRONTIERS.csv CALIBRATION_ABLATIONS.csv DOMAIN_GENERALIZATION_MATRIX.csv
MODEL_PROMOTION_GATES.json DEVELOPMENT_SCORING_RECEIPT.json SOURCE_SPLIT_VERIFICATION.json
SLURM_EXECUTION_LEDGER.csv FINETUNING_EXPERIMENTS.csv FIT_CLASSWISE_ERROR_AUDIT.csv FINETUNING_LEARNING_CURVES.csv
EXPERIMENT_CHECKPOINT_SHA256SUMS.txt TRAINING_SEEDS_AND_VARIANCE.csv FIT_FAILURES.json
FINAL_SELECTION_RECEIPT.json CANDIDATE_SCORING_RECEIPT.json
""".split())


def check_fields(keys):
    if {str(k).lower() for k in keys} & PRIVATE_FIELDS:
        raise ValueError("individual fields in aggregate evidence")


def json_value(value):
    if isinstance(value, dict):
        check_fields(value)
        for item in value.values():
            json_value(item)
    elif isinstance(value, list):
        for item in value:
            json_value(item)
    elif isinstance(value, str):
        if re.search(r"(/home/|/scratch/|[A-Za-z]:\\|BEGIN .{1,60}PRIVATE KEY|gh[pousr]_[A-Za-z0-9]{20,})", value):
            raise ValueError("private path or credential in delivery")


def rows(path):
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        check_fields(reader.fieldnames or ())
        result = list(reader)
        json_value(result)
        return result


def check_counts(row, sensitivity="recall", ppv="precision", empty_is_zero=False):
    tp, tn, fp, fn = (int(row[key]) for key in ("tp", "tn", "fp", "fn"))
    if min(tp, tn, fp, fn) < 0:
        raise ValueError("negative confusion cell")
    if "positive_support" in row and (tp + fn != int(row["positive_support"]) or tn + fp != int(row["negative_support"])):
        raise ValueError("confusion supports disagree")
    expected = {sensitivity: (tp, tp + fn), ppv: (tp, tp + fp), "f1": (2 * tp, 2 * tp + fp + fn),
                "specificity": (tn, tn + fp)}
    for key, (n, d) in expected.items():
        if key not in row:
            continue
        target = n / d if d else 0 if key == "f1" or empty_is_zero else None
        if (target is None and row[key] != "") or (target is not None and
                (row[key] == "" or not math.isclose(float(row[key]), target, abs_tol=1e-12))):
            raise ValueError(f"confusion-derived {key} disagrees")


def verify(folder):
    cfg = json.loads(PROTOCOL.read_bytes())
    receipt = json.loads((folder / "PUBLIC_VERIFICATION_RECEIPT.json").read_bytes())
    json_value(receipt)
    assert_hash(PROTOCOL, receipt["protocol_sha256"])
    names = set(receipt["sha256"])
    if (not names <= PUBLIC_FILES or {p.name for p in folder.iterdir()} != names | {"PUBLIC_VERIFICATION_RECEIPT.json"}
            or receipt["old_test_opened"] or receipt["independent_confirmation"] != "NOT_EVALUATED"):
        raise ValueError("delivery roster or access claim is invalid")
    for name, digest in receipt["sha256"].items():
        path = folder / name
        if not path.is_file() or path.is_symlink():
            raise ValueError("unexpected evidence file type")
        assert_hash(path, digest)
        if path.suffix == ".json":
            json_value(json.loads(path.read_bytes()))
        elif path.suffix == ".csv":
            rows(path)
    for name in ("CLASSWISE_FAILURE_DIAGNOSIS.csv", "CLASSWISE_FALSE_POSITIVE_FALSE_NEGATIVE_AUDIT.csv",
                 "DOMAIN_GENERALIZATION_MATRIX.csv", "FIT_CLASSWISE_ERROR_AUDIT.csv"):
        if name in names:
            for row in rows(folder / name):
                check_counts(row)
    for row in rows(folder / "THRESHOLD_SENSITIVITY_PRECISION_FRONTIERS.csv"):
        check_counts(row, "sensitivity", "ppv", empty_is_zero=True)
    jobs = rows(folder / "SLURM_EXECUTION_LEDGER.csv")
    by_job = {j["JobIDRaw"]: j for j in jobs}
    seconds = sum(int(r["ElapsedRaw"]) for r in jobs if "gres/gpu" in r["AllocTRES"])
    if len(by_job) != len(jobs) or seconds != receipt["gpu_allocation_seconds"] or seconds > 3600 * cfg["training"]["max_gpu_allocation_hours"]:
        raise ValueError("job ledger or GPU budget does not reconcile")
    if "FINETUNING_EXPERIMENTS.csv" not in names:
        return
    runs = rows(folder / "FINETUNING_EXPERIMENTS.csv")
    hashes, variance, seen, curves = {}, defaultdict(list), set(), defaultdict(list)
    for curve in rows(folder / "FINETUNING_LEARNING_CURVES.csv"):
        curves[curve["mode"], curve["seed"]].append(curve)
    for r in runs:
        mode, seed = r["mode"], r["seed"]
        key = mode, seed
        if (key in seen or int(seed) not in cfg["training"]["seeds"] or mode not in cfg["training"]["screen"]
                or any(r[k] != v for k, v in cfg["training"]["screen"][mode].items())
                or r["parent_sha256"] != cfg["parent_checkpoints"][seed]
                or not HEX.fullmatch(r["checkpoint_sha256"]) or not HEX.fullmatch(r["curves_sha256"])
                or r["slurm_job"] not in by_job):
            raise ValueError("fit receipt does not match frozen protocol")
        seen.add(key)
        epochs = curves.pop(key)
        best = max(epochs, key=lambda e: (float(e["macro_ap"]), float(e["guard_ap"])))
        if ([int(e["epoch"]) for e in epochs] != list(range(1, len(epochs) + 1))
                or len(epochs) > cfg["training"]["epochs"]
                or best["epoch"] != r["best_epoch"]
                or float(best["macro_ap"]) != float(r["validation_macro_ap"])
                or float(best["guard_ap"]) != float(r["validation_guard_ap"])):
            raise ValueError("best epoch does not match the learning curve")
        hashes[f"{mode}-{seed}/best.pt"] = r["checkpoint_sha256"]
        variance[mode].append(float(r["validation_macro_ap"]))
    if (curves or len(runs) != receipt["checked_fits"]
            or len(runs) + receipt["failed_fits"] > cfg["training"]["max_supervised_fits"]):
        raise ValueError("fit budget or receipt mismatch")
    sums = [line.split("  ", 1) for line in (folder / "EXPERIMENT_CHECKPOINT_SHA256SUMS.txt").read_text().splitlines()]
    if len(sums) != len(runs) or {name: sha for sha, name in sums} != hashes:
        raise ValueError("checkpoint hashes do not match fitted models")
    for r in rows(folder / "TRAINING_SEEDS_AND_VARIANCE.csv"):
        values = variance.pop(r["mode"])
        if (int(r["n_seeds"]) != len(values) or float(r["mean_validation_macro_ap"]) != mean(values)
                or (float(r["sample_sd_validation_macro_ap"]) if len(values) > 1 else None)
                != (stdev(values) if len(values) > 1 else None)):
            raise ValueError("seed statistics do not reconcile")
    if variance:
        raise ValueError("missing seed statistics")
    gates = json.loads((folder / "MODEL_PROMOTION_GATES.json").read_bytes())
    if gates["old_test_opened"] or gates["promotion"] != "NOT_AUTHORIZED":
        raise ValueError("promotion exceeds the study scope")
    if "C" in gates["code_validation"]:
        selection_path = folder / "FINAL_SELECTION_RECEIPT.json"
        final = json.loads(selection_path.read_bytes())
        candidate = json.loads((folder / "CANDIDATE_SCORING_RECEIPT.json").read_bytes())
        selected = final["selected"]
        assert_hash(selection_path, candidate["selection_sha256"])
        name = f"{candidate['mode']}-{candidate['seed']}/best.pt"
        if (candidate["old_test_opened"] or not candidate["candidate_calibration_scored_after_selection"]
                or hashes.get(name) != selected["representative_sha256"]
                or selected["representative_sha256"] != candidate["checkpoint_sha256"]
                or {int(r["seed"]) for r in runs if r["mode"] == selected["mode"]} != set(cfg["training"]["seeds"])):
            raise ValueError("candidate calibration does not follow the sealed three-seed selection")
    domains = rows(folder / "DOMAIN_GENERALIZATION_MATRIX.csv")
    for arm, summary in gates["code_validation"].items():
        selected = [r for r in domains if r["arm"] == arm and r["scope"] == "validation"]
        if {r["endpoint"] for r in selected} != set(cfg["endpoints"]) or len(selected) != len(cfg["endpoints"]):
            raise ValueError("CODE validation endpoint roster differs")
        for key in ("f1", "raw_auprc", "brier_score", "ece"):
            if not math.isclose(summary[f"macro_{key}"], mean(float(r[key]) for r in selected), abs_tol=1e-12):
                raise ValueError("macro metrics do not reconcile")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    verify(parser.parse_args().folder)
    print("Public recovery evidence verified")
