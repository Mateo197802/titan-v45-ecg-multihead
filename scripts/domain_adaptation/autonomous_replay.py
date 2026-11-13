"""Replay a sealed composite on a deterministic development sample."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import numpy as np
import torch
from autonomous_export import ancestry
from autonomous_worker import PROTOCOL, Runner, Specialist, read_fit
from recovery_inputs import config, parent_model
from recovery_training import aux_data
from train_duration_aware import digest, write_json


def checkpoint_endpoint(runner, path, fit, scope, samples):
    state = torch.load(path / "best.pt", map_location="cuda", weights_only=True)
    seed, arm, endpoint = fit["seed"], fit["arm"], fit["endpoint"]
    if (state["seed"], state["arm"], state["endpoint"], state["protocol_sha256"]) != (
        seed, arm, endpoint, digest(PROTOCOL)
    ) or state["ancestor_checkpoint_sha256"] != fit["anchor_sha256"]:
        raise ValueError("checkpoint replay metadata mismatch")
    model = parent_model(runner.previous, seed).cuda().eval().requires_grad_(False)
    readout = Specialist(model.backbone.d_model, arm).cuda().eval()
    readout.load_state_dict(state["readout"], strict=True)
    changes = state["backbone_updates"]
    if set(changes) - dict(model.backbone.named_parameters()).keys():
        raise ValueError("unknown backbone update key")
    normalizer = "robust_shared_gain" if arm == "shared_gain" else "per_lead_zscore"
    rr = aux_data(runner.archive, scope)[0] if arm == "rr_temporal" else None
    outputs = []
    with torch.inference_mode():
        for feat, old, wave, _, _, exams, _ in runner.features(scope, normalizer, seed, model)[:samples]:
            x = torch.as_tensor(wave, device="cuda")
            if changes:
                for name, p in model.backbone.named_parameters():
                    if name in changes:
                        p.copy_(changes[name])
                v = model.backbone.forward_features(x)
            else:
                v = torch.as_tensor(feat, device="cuda")
            proxy = torch.as_tensor(np.asarray([rr[str(k)] for k in exams]), device="cuda") if rr else None
            z = readout(v, x, proxy)
            if arm in {"residual", "late"}:
                j = config()["endpoints"].index(endpoint)
                z = z + torch.logit(torch.as_tensor(old[:, j], device="cuda").clamp(1e-6, 1 - 1e-6))
            outputs.append(z.sigmoid().cpu().numpy())
    return np.concatenate(outputs)


def run(previous, archive, root, output):
    data = json.loads((root / "final.json").read_bytes())
    if data["historical_test_opened"] or data["state"]["protocol_sha256"] != digest(PROTOCOL):
        raise ValueError("invalid replay boundary")
    runner = Runner(previous, archive)
    chain = ancestry(data["fits"], data["finalist"])
    if not chain:
        raise ValueError("no trained composite to replay")
    error, counts = 0., {}
    for scope in ("validation", "chapman", "cpsc"):
        reference = runner.data[scope]["p"]
        rebuilt = reference[:64].copy()
        used = set()
        for name in chain:
            path = root / "fits" / name
            fit = read_fit(path)
            j = config()["endpoints"].index(fit["endpoint"])
            if j not in used:
                got = checkpoint_endpoint(runner, path, fit, scope, 1)
                if len(got) != len(rebuilt):
                    raise ValueError("replay sample count differs")
                rebuilt[:, j] = got
                used.add(j)
        with np.load(root / "fits" / chain[0] / "private_scores.npz", allow_pickle=False) as z:
            error = max(error, float(np.max(np.abs(rebuilt - z[scope][:64]))))
        counts[scope] = len(rebuilt)
    if error > 1e-5:
        raise ValueError(f"checkpoint inference replay exceeded 1e-5: {error}")
    write_json(output, {"protocol_sha256": digest(PROTOCOL), "slurm_job": os.getenv("SLURM_JOB_ID"),
                        "finalist": data["finalist"], "chain": chain, "sample_counts": counts,
                        "max_absolute_probability_error": error, "test_opened": False})


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for arg in ("previous", "archive", "root", "output"):
        p.add_argument(arg, type=Path)
    run(**vars(p.parse_args()))
