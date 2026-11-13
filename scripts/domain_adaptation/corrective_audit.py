"""Audit the sealed development pipeline before authorizing corrective fitting."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from recovery_calibration import baseline_metrics, bm, guard_limits, load_score, operating_frontier
from recovery_inputs import (
    RECOVERY,
    ROOT,
    audit_splits,
    authorized_bank,
    config,
    parent_model,
    score_model,
)
from recovery_reporting import source_audit
from recovery_training import RecoveryNet, depth_settings
from train_duration_aware import batches, digest, write_json

PROTOCOL = ROOT / "docs/performance_recovery/CORRECTIVE_PROTOCOL.json"


def cfg():
    data = json.loads(PROTOCOL.read_bytes())
    if digest(RECOVERY) != data["parent_protocol_sha256"]:
        raise ValueError("parent protocol seal mismatch")
    return data


def gradients(model, sample):
    for name, value in model.named_parameters():
        _, epoch = depth_settings(name, 1, "progressive", cfg()["optimization"])
        value.requires_grad_(epoch == 1)
    x, d, y = (torch.as_tensor(v, device="cuda") for v in sample[:3])
    if not torch.all(torch.isin(y, y.new_tensor([-1, 0, 1]))):
        raise ValueError("invalid masked label values")
    y = y.clone()
    y[0, 0] = -1
    model.eval()
    z = model(x, d)
    z.retain_grad()
    (F.binary_cross_entropy_with_logits(z, y.clamp_min(0), reduction="none") * (y >= 0)).mean().backward()
    if torch.any(z.grad[y < 0] != 0):
        raise ValueError("masked cell propagated gradient")
    report = {}
    for name, parameter in model.named_parameters():
        key = ".".join(name.split(".")[:4]) if name.startswith("base.backbone.") else "head"
        cell = report.setdefault(key, dict(active=0, frozen=0, nonzero=0, disconnected=0, nonfinite=0))
        cell["active" if parameter.requires_grad else "frozen"] += parameter.numel()
        grad = parameter.grad
        if grad is None:
            cell["disconnected"] += int(parameter.requires_grad)
        else:
            if not parameter.requires_grad:
                raise ValueError("frozen parameter received gradient")
            cell["nonfinite"] += int(not torch.isfinite(grad).all())
            cell["nonzero"] += int(torch.any(grad != 0))
    if any(r["nonfinite"] or r["disconnected"] or (r["active"] and not r["nonzero"]) for r in report.values()):
        raise ValueError("gradient audit failed")
    return report


def diagnose(previous, archived, output):
    c = cfg()
    bank = previous / "code-bank"
    split = audit_splits(bank)
    source = source_audit(previous / "additional-sources-v2")
    validation = authorized_bank(bank, "validation", "per_lead_zscore")
    baseline = parent_model(previous, c["seeds"][0]).cuda().eval()
    wrapped = RecoveryNet(baseline, "shared").cuda().eval()
    current = score_model(wrapped, validation)
    val = load_score(archived, "validation")
    if any(not np.array_equal(current[k], val[k]) for k in ("exams", "labels", "patients", "durations")):
        raise ValueError("development rows changed")
    error = float(np.max(np.abs(current["p"] - val["p"])))
    if error > 1e-5:
        raise ValueError(f"incumbent replay outside bound: {error}")
    by_class = {}
    receipt = json.loads((archived / "DEVELOPMENT_SCORING_RECEIPT.json").read_bytes())
    for j, endpoint in enumerate(c["endpoints"]):
        y, p = val["labels"][:, j], val["p"][:, j]
        keep = y >= 0
        y, p = y[keep], p[keep]
        cut = config()["incumbent_thresholds"][j]
        f = operating_frontier(y, p, guard_limits(baseline_metrics(val, j, endpoint, receipt), endpoint))
        feasible = f["feasible"]
        by_class[endpoint] = {
            "original_cut": cut, "original": bm(y, p, cut), "validation_oracle_only": True,
            "feasible_threshold_exists": bool(feasible.any()),
            "max_feasible_f1": float(f["f1"][feasible].max()) if feasible.any() else None,
            "margin_by_outcome": {
                name: {"n": int(mask.sum()), "mean": float(np.mean(p[mask] - cut)) if mask.sum() >= 10 else None}
                for name, mask in {"tp": (y == 1) & (p >= cut), "fn": (y == 1) & (p < cut),
                                   "tn": (y == 0) & (p < cut), "fp": (y == 0) & (p >= cut)}.items()},
        }
    chap = load_score(archived, "chapman")
    sb, prob = chap["labels"][:, 1], chap["p"][:, 1]
    keep = sb >= 0
    frontier = operating_frontier(sb[keep], prob[keep], {"ppv_min": .30, "sensitivity_min": .20})
    ap = bm(sb[keep], prob[keep], .87)["average_precision"]
    group_gradients = {str(length): gradients(
        RecoveryNet(parent_model(previous, c["seeds"][0]), "shared").cuda(),
        next(batches({length: data}, 8))) for length, data in validation.items()}
    result = {"protocol_sha256": digest(PROTOCOL), "slurm_job": os.getenv("SLURM_JOB_ID"),
              "diagnostic_pass": True, "test_opened": False, "max_probability_replay_error": error,
              "checkpoint_tensor_count": len(baseline.state_dict()),
              "parameters": sum(p.numel() for p in baseline.parameters()), "splits": split, "sources": source,
              "gradient_groups_by_samples": group_gradients, "masked_gradient_zero": True,
              "class_diagnosis": by_class, "chapman_sb_ap": ap,
              "chapman_sb_frontier_has_feasible": bool(frontier["feasible"].any()),
              "allow_source": bool(ap >= .5 and frontier["feasible"].any())}
    write_json(output, result)
    print(json.dumps({k: result[k] for k in ("diagnostic_pass", "max_probability_replay_error", "allow_source")}))


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    for arg in ("previous", "archived", "output"):
        cli.add_argument(arg, type=Path)
    diagnose(**vars(cli.parse_args()))
