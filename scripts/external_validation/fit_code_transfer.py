"""Train fixed residual specialists on verified Stage A development features only."""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from code15_io import PROTOCOL, ROOT, digest
from scipy.optimize import minimize
from scipy.special import expit

sys.path.insert(0, str(ROOT / "src"))
from titan_v45.models.frozen_rhythm import P8_CLASSES


def residual_logits(features, baseline, mean, scale, coefficients, cap):
    return baseline + cap * np.tanh(((features - mean) / scale) @ coefficients[:-1] + coefficients[-1])


def fit_endpoint(x, baseline, y, weight, *, cap, l2, maxiter):
    weight = weight / weight.sum()

    def objective(theta):
        latent = x @ theta[:-1] + theta[-1]
        t = np.tanh(latent)
        logits = baseline + cap * t
        loss = np.dot(weight, np.logaddexp(0, logits) - y * logits)
        derivative = weight * (expit(logits) - y) * cap * (1 - t * t)
        gradient = np.r_[x.T @ derivative, derivative.sum()] + l2 * theta
        return float(loss + l2 * np.dot(theta, theta) / 2), gradient

    result = minimize(objective, np.zeros(x.shape[1] + 1), method="L-BFGS-B", jac=True,
                      options={"maxiter": maxiter})
    if not result.success or not np.isfinite(result.x).all():
        raise RuntimeError(f"residual fit failed: optimizer status {result.status}")
    return result.x, int(result.nit)


def run(cache: Path, output: Path):
    protocol = json.loads(PROTOCOL.read_bytes())
    rule = protocol["candidate"]
    cap = float(rule["residual_logit_cap"])
    features_path = cache / "private_frozen_features.npz"
    metadata_path = cache / "private_feature_metadata.json"
    metadata = json.loads(metadata_path.read_bytes())
    if digest(features_path) != metadata["feature_cache_sha256"]:
        raise ValueError("stage A feature-cache integrity failure")
    rows = metadata["rhythm_records"]
    selected = {
        split: {i for i, row in enumerate(rows) if row["scored"] and row["split"] == split
                and row["source"] in ({"chapman_shaoxing", "cpsc2018"} if split == "train" else {"chapman_shaoxing"})}
        for split in ("train", "validation")
    }
    if any(not group for group in selected.values()) or selected["train"] & selected["validation"]:
        raise ValueError("development split invariant failed")
    grouped = [{rows[i]["group_hash"] for i in group if rows[i].get("group_hash")}
               for group in selected.values()]
    if grouped[0] & grouped[1]:
        raise ValueError("development patient-group overlap")
    endpoints = list(protocol["reference"])
    columns = [P8_CLASSES.index(endpoint) for endpoint in endpoints]
    receipt = {"scope": "DEVELOPMENT_ONLY_FROZEN_RESIDUAL",
               "protocol_sha256": digest(PROTOCOL),
               "feature_cache_sha256": metadata["feature_cache_sha256"],
               "feature_metadata_sha256": digest(metadata_path),
               "records": {key: len(value) for key, value in selected.items()},
               "endpoints": endpoints, "profiles": {},
               "code_or_mimic_outcomes_used": False, "thresholds_changed": False}
    output.mkdir(mode=0o700, exist_ok=False)
    with np.load(features_path, allow_pickle=False) as arrays:
        record_indices = arrays["rhythm_record_index"]
        window_ids = {s: np.flatnonzero(np.isin(record_indices, list(ids))) for s, ids in selected.items()}
        train, validation = window_ids["train"], window_ids["validation"]
        train_ids = record_indices[train]
        val_ids = record_indices[validation]
        multiplicity = Counter(train_ids.tolist())
        weights = np.array([1 / multiplicity[i] for i in train_ids])
        sources = np.array([rows[i]["source"] for i in train_ids])
        for profile in protocol["evaluation"]["profiles"]:
            prefix = profile.lower()
            x, xv = (arrays[prefix + "_features"][idx].astype(np.float64) for idx in (train, validation))
            old, oldv = (arrays[prefix + "_baseline_logits"][idx][:, columns].astype(np.float64)
                         for idx in (train, validation))
            mean = np.average(x, weights=weights, axis=0)
            scale = np.sqrt(np.average((x - mean) ** 2, weights=weights, axis=0)).clip(1e-3)
            x = (x - mean) / scale
            result, fit_stats = [], {}
            for j, (endpoint, col) in enumerate(zip(endpoints, columns, strict=True)):
                keep = np.asarray([bool(rows[i]["mask"][col]) for i in train_ids])
                y = np.asarray([int(rows[i]["targets"][col]) for i in train_ids[keep]])
                if set(y) != {0, 1}:
                    raise ValueError(f"insufficient development supervision: {profile}/{endpoint}")
                w = weights[keep].copy()
                # Equal observed source contribution, capped positive reweighting.
                for source in np.unique(sources[keep]):
                    at = sources[keep] == source
                    w[at] /= w[at].sum()
                w[y == 1] *= np.clip(w[y == 0].sum() / w[y == 1].sum(), 1, 4)
                theta, iterations = fit_endpoint(x[keep], old[keep, j], y, w, cap=cap,
                                                 l2=rule["l2"], maxiter=rule["maximum_iterations"])
                result.append(theta)
                vk = np.asarray([bool(rows[i]["mask"][col]) for i in val_ids])
                vy = np.asarray([int(rows[i]["targets"][col]) for i in val_ids[vk]])
                vl = residual_logits(xv[vk], oldv[vk, j], mean, scale, theta, cap)
                fit_stats[endpoint] = {"iterations": iterations, "train_observed_windows": int(keep.sum()),
                                       "validation_observed_windows": int(vk.sum()),
                                       "validation_window_bce": float(np.mean(np.logaddexp(0, vl) - vy * vl)) if len(vl) else None}
            artifact = output / f"{profile}.npz"
            np.savez(artifact, mean=mean, scale=scale, coefficients=np.stack(result, axis=1),
                     endpoints=np.asarray(endpoints), cap=np.asarray(cap))
            receipt["profiles"][profile] = {"sha256": digest(artifact), "fit": fit_stats}
    text = json.dumps(receipt, sort_keys=True, indent=2) + "\n"
    (output / "candidate_receipt.json").write_bytes(text.encode())
    print(text, end="")


if __name__ == "__main__":
    os.umask(0o077)
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("cache", type=Path)
    cli.add_argument("output", type=Path)
    args = cli.parse_args()
    run(args.cache, args.output)
