"""Fit targeted corrections and choose epochs without opening calibration."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from corrective_audit import PROTOCOL, cfg
from recovery_calibration import (
    baseline_metrics,
    bm,
    choose_cut,
    grouped_folds,
    guard_limits,
    load_score,
    operating_frontier,
)
from recovery_inputs import ROOT, parent_model, score_model
from recovery_training import RecoveryNet, depth_settings, get_code, get_other, stream_batches
from train_duration_aware import digest, write_json


def masks(y, parent, hp):
    focus = (y == 1) & (parent <= hp["hard_positive_probability_max"])
    focus |= (y == 0) & (parent >= hp["hard_negative_probability_min"])
    focus[:, 2:4] = False
    return focus, y >= 0


def oof(data, prob, receipt):
    fold = grouped_folds(data["patients"])
    rows = []
    for k in range(3):
        train = {key: arr[fold != k] for key, arr in data.items()}
        valid = {key: arr[fold == k] for key, arr in data.items()}
        for j, endpoint in enumerate(cfg()["endpoints"]):
            a, b = train["labels"][:, j] >= 0, valid["labels"][:, j] >= 0
            fit_truth, eval_truth = train["labels"][a, j], valid["labels"][b, j]
            if min(len(set(fit_truth)), len(set(eval_truth))) < 2:
                raise ValueError("selection fold lacks endpoint support")
            fit_cut = choose_cut(fit_truth, prob[fold != k, j][a], guard_limits(
                baseline_metrics(train, j, endpoint, receipt), endpoint))
            metrics = operating_frontier(eval_truth, prob[fold == k, j][b], guard_limits(
                baseline_metrics(valid, j, endpoint, receipt), endpoint), np.array([fit_cut["threshold"]]))
            rows.append((bool(metrics["feasible"][0]), float(metrics["guard_deficit"][0]), float(metrics["f1"][0])))
    ap = []
    for j in range(prob.shape[1]):
        y = data["labels"][:, j]
        valid = y >= 0
        ap.append(bm(y[valid], prob[valid, j], .5)["average_precision"])
    return [sum(not r[0] for r in rows), sum(r[1] for r in rows), float(np.mean([r[2] for r in rows])), float(np.mean(ap))]


def train(previous, archived, audit, output, arm, seed):
    c = cfg()
    report = json.loads(audit.read_bytes())
    if (report["protocol_sha256"] != digest(PROTOCOL) or not report["diagnostic_pass"]
            or report["test_opened"] or arm not in c["arms"] or seed not in c["seeds"]):
        raise ValueError("corrective diagnostic or scope gate failed")
    if arm == "targeted_source" and not report["allow_source"]:
        print("Source gate did not pass; no fit", flush=True)
        return
    output.mkdir(mode=0o700, exist_ok=False)
    hp = c["optimization"]
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    rng = np.random.default_rng(seed)
    norm = "per_lead_zscore"
    code = get_code(previous, "train", norm)
    train_banks = {"code": code}
    if arm == "targeted_source":
        train_banks["chapman"] = get_other(previous, "chapman_shaoxing", "train", norm)
    validation = get_code(previous, "validation", norm)
    ref = load_score(archived, "validation")
    receipt = json.loads((archived / "DEVELOPMENT_SCORING_RECEIPT.json").read_bytes())
    base = RecoveryNet(parent_model(previous, seed), "shared").cuda().eval().requires_grad_(False)
    model = RecoveryNet(parent_model(previous, seed), "shared").cuda()
    groups = []
    for name, parameter in model.named_parameters():
        lr, epoch = depth_settings(name, 1, "progressive", hp)
        parameter.requires_grad_(epoch == 1)
        if lr:
            groups.append({"params": [parameter], "lr": lr, "start_epoch": epoch})
    optim = torch.optim.AdamW(groups, weight_decay=hp["weight_decay"])
    weights = {}
    for source, bank in train_banks.items():
        y = np.concatenate([a[2] for a in bank.values()])
        weights[source] = torch.as_tensor(np.sqrt((y == 0).sum(axis=0) / (y == 1).sum(axis=0)).clip(1, 12),
                                          device="cuda", dtype=torch.float32)
    best, history = None, []
    for epoch in range(1, c["epochs"] + 1):
        for group in groups:
            group["params"][0].requires_grad_(epoch >= group["start_epoch"])
        model.train()
        model.base.backbone.eval()
        total, n, hard_counts, max_grad = 0., 0, np.zeros(5, dtype=int), 0.
        for source, (wave, desc, label, w, *_) in stream_batches(
                train_banks, hp["batch_size"], rng, hp["external_batch_fraction"]):
            x, d, y, weight = [torch.as_tensor(v, device="cuda") for v in (wave, desc, label, w)]
            optim.zero_grad(set_to_none=True)
            with torch.autocast("cuda", dtype=torch.bfloat16, enabled=torch.cuda.is_bf16_supported()):
                with torch.no_grad():
                    z0 = base(x, d).float()
                z = model(x, d).float()
                hard, known = masks(y, z0.sigmoid(), hp)
                wgt = known * weight[:, None] * torch.where(hard, hp["hard_weight"], 1.)
                ce = F.binary_cross_entropy_with_logits(z, y.clamp_min(0), pos_weight=weights[source], reduction="none")
                protect = F.mse_loss(z[:, 2:4], z0[:, 2:4])
                loss = (ce * wgt).sum() / wgt.sum().clamp_min(1) + hp["protected_logit_mse_weight"] * protect
            if not torch.isfinite(loss):
                raise FloatingPointError("nonfinite corrective loss")
            loss.backward()
            norm_g = torch.nn.utils.clip_grad_norm_(model.parameters(), hp["gradient_clip"], error_if_nonfinite=True)
            optim.step()
            total += float(loss.detach())
            n += 1
            hard_counts += hard.sum(dim=0).cpu().numpy()
            max_grad = max(max_grad, float(norm_g))
        scored = score_model(model, validation)
        if any(not np.array_equal(scored[key], ref[key]) for key in ("exams", "labels", "patients")):
            raise ValueError("corrective validation row mismatch")
        values = oof(ref, scored["p"], receipt)
        row = {"epoch": epoch, "loss": total / n, "hard_cells": hard_counts.tolist(), "max_gradient": max_grad,
               "trainable": sum(p.numel() for p in model.parameters() if p.requires_grad), "selection": values}
        history.append(row)
        print(json.dumps({"arm": arm, "seed": seed, **row}), flush=True)
        rank = (values[0], values[1], -values[2], -values[3])
        if best is None or rank < best[0]:
            best = rank, row
            torch.save({"state_dict": model.state_dict(), "protocol_sha256": digest(PROTOCOL),
                        "arm": arm, "seed": seed, "epoch": epoch}, output / "best.pt")
            np.savez_compressed(output / "private_validation.npz", **scored)
    write_json(output / "fit.json", {
        "arm": arm, "seed": seed, "slurm_job": os.getenv("SLURM_JOB_ID"), "epoch": best[1],
        "history": history, "checkpoint_sha256": digest(output / "best.pt"),
        "validation_scores_sha256": digest(output / "private_validation.npz"),
        "protocol_sha256": digest(PROTOCOL), "audit_sha256": digest(audit),
        "calibration_opened": False, "test_opened": False,
        "code_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()})


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    for arg in ("previous", "archived", "audit", "output"):
        cli.add_argument(arg, type=Path)
    cli.add_argument("arm", choices=tuple(cfg()["arms"]))
    cli.add_argument("seed", type=int, choices=cfg()["seeds"])
    args = vars(cli.parse_args())
    root = args["output"]
    if sum(path.is_dir() for path in root.glob("*")) >= cfg()["max_fits"]:
        raise ValueError("corrective fit budget exhausted")
    root.mkdir(mode=0o700, exist_ok=True)
    args["output"] = root / f"{args['arm']}-{args['seed']}"
    train(**args)
