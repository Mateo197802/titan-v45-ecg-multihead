"""Compare separability in frozen embeddings, descriptors and incumbent scores."""
from __future__ import annotations

import argparse
import os
from pathlib import Path

import numpy as np
import torch
from corrective_audit import PROTOCOL, cfg
from recovery_calibration import bm, csv_write
from recovery_inputs import ROOT, parent_model
from recovery_training import get_code, get_other
from scipy.optimize import minimize
from scipy.special import expit
from train_duration_aware import batches, digest, write_json

from titan_v45.models.frozen_pathology import verified_assets

ASSETS = {"backbone-v3f-original.pt", "backbone-v3ag-pathology.pt", "specialists-v3ag-primary4-calibrated.pt",
          "specialists-v3p-e008-primary6-diagnostic.pt", "specialists-v3q-primary8-best-candidate.pt"}


def extract(model, bank):
    values = []
    with torch.inference_mode():
        for x, d, y, *_ in batches(bank, 32):
            waveform, desc = (torch.as_tensor(v, device="cuda") for v in (x, d))
            embedding = model.backbone.forward_features(waveform)
            length = embedding.new_zeros((len(x), 2))
            length[:, int(x.shape[-1] == 1250)] = 1
            joined = torch.cat((embedding, desc, length), dim=1)
            p = model.head(joined).sigmoid()
            values.append((embedding.cpu().numpy(), d, p.cpu().numpy(), y))
    return tuple(np.concatenate(arrays) for arrays in zip(*values, strict=True))


def linear_probe(x, y, evaluation):
    x, evaluation = x.astype(np.float64), evaluation.astype(np.float64)
    mu, sd = x.mean(axis=0), x.std(axis=0).clip(1e-6)
    x, evaluation = (x - mu) / sd, (evaluation - mu) / sd

    def objective(beta):
        z = x @ beta[:-1] + beta[-1]
        resid = expit(z) - y
        value = np.mean(np.logaddexp(0, z) - y * z) + .01 * np.dot(beta[:-1], beta[:-1])
        gradient = np.r_[x.T @ resid / len(y) + .02 * beta[:-1], resid.mean()]
        return value, gradient

    fit = minimize(objective, np.zeros(x.shape[1] + 1), jac=True, method="L-BFGS-B")
    if not fit.success:
        raise ValueError("fixed diagnostic probe did not converge")
    return expit(evaluation @ fit.x[:-1] + fit.x[-1])


def run(previous, assets, output):
    output.mkdir(mode=0o700, exist_ok=False)
    _, hashes = verified_assets(ROOT, assets, ASSETS)
    model = parent_model(previous, cfg()["seeds"][0]).cuda().eval()
    train = extract(model, get_code(previous, "train", "per_lead_zscore"))
    cohorts = {
        "code_train_apparent": train,
        "code_validation": extract(model, get_code(previous, "validation", "per_lead_zscore")),
        "chapman_development": extract(model, get_other(previous, "chapman_shaoxing", "validation", "per_lead_zscore")),
        "cpsc_development": extract(model, get_other(previous, "cpsc2018", "train", "per_lead_zscore")),
    }
    rows = []
    for j, e in enumerate(cfg()["endpoints"]):
        for scope, data in cohorts.items():
            valid = data[3][:, j] >= 0
            y = data[3][valid, j]
            if len(set(y)) < 2:
                continue
            known = train[3][:, j] >= 0
            probes = {"incumbent": data[2][valid, j]}
            for idx, name in enumerate(("embedding_linear", "descriptor_linear")):
                probes[name] = linear_probe(train[idx][known], train[3][known, j], data[idx][valid])
            for name, p in probes.items():
                r = bm(y, p, .5)
                rows.append({"scope": scope, "endpoint": e, "readout": name, **{k: r[k] for k in
                             ("positive_support", "negative_support", "auroc", "average_precision")}})
    path = output / "CORRECTIVE_REPRESENTATION_PROBE.csv"
    csv_write(path, rows)
    write_json(output / "CORRECTIVE_REPRESENTATION_RECEIPT.json", {
        "protocol_sha256": digest(PROTOCOL), "slurm_job": os.getenv("SLURM_JOB_ID"), "published_weights": hashes,
        "results_sha256": digest(path), "test_opened": False,
        "scope": "retrospective diagnostic only; not used to select fits or thresholds",
        "method": "CODE-train-only logistic readouts, standardization fitted on train, fixed L2=0.01, no grid search"})


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    for name in ("previous", "assets", "output"):
        cli.add_argument(name, type=Path)
    run(**vars(cli.parse_args()))
