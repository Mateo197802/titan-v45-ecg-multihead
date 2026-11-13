"""Train and diagnose a bounded MLP residual ablation without access to CODE."""
from __future__ import annotations

import argparse
import csv
import json
import os
from collections import Counter
from pathlib import Path

import numpy as np
import torch
from code15_io import PROTOCOL, ROOT, digest
from evaluate_code15 import paired_metrics
from fit_code_transfer import P8_CLASSES, residual_logits
from scipy.special import expit
from torch import nn
from torch.nn import functional as F

FREEZE = ROOT / "docs/external_validation_20261111/FROZEN_DEVELOPMENT_ABLATION.json"


def aggregate(values, indices, total, profile):
    combined = np.zeros((total, values.shape[1]), dtype=np.float64)
    np.add.at(combined, indices, values if profile == "P6" else expit(values))
    combined /= np.bincount(indices, minlength=total)[:, None]
    return expit(combined) if profile == "P6" else combined


def load_split(arrays, rows, profile, columns, selected, mean, scale):
    links = arrays["rhythm_record_index"]
    ids = np.flatnonzero(np.isin(links, selected))
    mapped = {value: idx for idx, value in enumerate(selected)}
    local = np.array([mapped[int(value)] for value in links[ids]], dtype=np.int64)
    records = [rows[i] for i in selected]
    labels = np.array([[int(r["targets"][c]) if r["mask"][c] else -1 for c in columns]
                       for r in records], dtype=np.int64)
    matrix = arrays[profile.lower() + "_features"][ids]
    old = arrays[profile.lower() + "_baseline_logits"][ids][:, columns]
    return matrix, ((matrix - mean) / scale).astype(np.float32), old, local, labels, records


def fit_variant(train, validation, profile, config, gamma):
    _, x, old, link, labels, records = train
    _, vx, vold, vl, vy, _ = validation
    counts = Counter(link.tolist())
    sources = np.asarray([records[i]["source"] for i in link])
    y = labels[link]
    if any(set(y[:, col]) & {0, 1} != {0, 1} for col in range(y.shape[1])):
        raise ValueError("missing supervised polarity in training")
    weights = np.zeros_like(y, dtype=np.float32)
    inv = np.asarray([1 / counts[i] for i in link], dtype=np.float32)
    for col in range(y.shape[1]):
        for source in set(sources):
            keep = (sources == source) & (y[:, col] >= 0)
            if keep.any():
                weights[keep, col] = inv[keep] / inv[keep].sum()
        positive = y[:, col] == 1
        weights[positive, col] *= np.clip(weights[y[:, col] == 0, col].sum() /
                                          weights[positive, col].sum(), 1, 4)
    torch.manual_seed(config["seed"])
    model = nn.Sequential(nn.Linear(x.shape[1], config["hidden_width"]), nn.SiLU(),
                          nn.Dropout(config["dropout"]), nn.Linear(config["hidden_width"], y.shape[1]))
    nn.init.zeros_(model[-1].weight)
    nn.init.zeros_(model[-1].bias)
    optimizer = torch.optim.AdamW(model.parameters(), lr=config["learning_rate"], weight_decay=config["weight_decay"])
    xt, ot, yt, wt = (torch.as_tensor(v, dtype=torch.float32) for v in (x, old, y.clip(0, 1), weights))
    best, epoch_best, frozen = np.inf, 0, None
    history = []
    rng = np.random.default_rng(config["seed"])
    for epoch in range(1, config["max_epochs"] + 1):
        model.train()
        for ids in np.array_split(rng.permutation(len(x)), (len(x) + config["batch_size"] - 1) // config["batch_size"]):
            z = ot[ids] + config["residual_cap"] * model(xt[ids]).tanh()
            per = F.binary_cross_entropy_with_logits(z, yt[ids], reduction="none")
            if gamma:
                per = per * torch.where(yt[ids] > 0, 1.0, z.sigmoid().pow(gamma))
            loss = (per * wt[ids]).sum() / wt[ids].sum().clamp_min(1e-12)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        model.eval()
        with torch.no_grad():
            vp = aggregate(vold + config["residual_cap"] * model(torch.from_numpy(vx)).tanh().numpy(),
                           vl, len(vy), profile).clip(1e-7, 1 - 1e-7)
        observed = vy >= 0
        score = float((-vy[observed] * np.log(vp[observed]) -
                       (1 - vy[observed]) * np.log1p(-vp[observed])).mean())
        if not np.isfinite(score):
            raise ValueError("nonfinite validation BCE")
        history.append(score)
        if score < best:
            best, epoch_best = score, epoch
            frozen = {key: value.clone() for key, value in model.state_dict().items()}
        if epoch - epoch_best >= config["patience"]:
            break
    model.load_state_dict(frozen)
    model.eval()
    return model, {"epoch": epoch_best, "validation_bce": best, "history": history}


def run(feature_dir: Path, linear_dir: Path, output: Path):
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    config = json.loads(FREEZE.read_bytes())
    protocol = json.loads(PROTOCOL.read_bytes())
    endpoints = config["classes"]
    if endpoints != list(protocol["reference"]):
        raise ValueError("development endpoint contract differs")
    columns = [P8_CLASSES.index(e) for e in endpoints]
    metadata = json.loads((feature_dir / "private_feature_metadata.json").read_bytes())
    array_path = feature_dir / "private_frozen_features.npz"
    line = json.loads((linear_dir / "candidate_receipt.json").read_bytes())
    if (digest(array_path) != metadata["feature_cache_sha256"]
            or line["feature_cache_sha256"] != metadata["feature_cache_sha256"]
            or line["protocol_sha256"] != digest(PROTOCOL) or line["code_or_mimic_outcomes_used"]):
        raise ValueError("development inputs do not match sealed cache")
    rows = metadata["rhythm_records"]
    selections = {
        "train": [i for i, r in enumerate(rows) if r["scored"] and r["split"] == config["training_split"]
                  and r["source"] in config["training_sources"]],
        "validation": [i for i, r in enumerate(rows) if r["scored"] and r["split"] == config["selection_split"]
                       and r["source"] == config["selection_source"]],
        "descriptive": [i for i, r in enumerate(rows) if r["scored"] and r["split"] == config["descriptive_split"]
                        and r["source"] == config["descriptive_source"]],
    }
    if any(not split for split in selections.values()) or len(set(sum(selections.values(), []))) != sum(
        map(len, selections.values())
    ):
        raise ValueError("missing or overlapping development splits")
    output.mkdir(mode=0o700, exist_ok=False)
    report = {"scope": config["scope"], "protocol_sha256": digest(FREEZE), "code15_inputs_opened": False,
              "mimic_inputs_opened": False, "split_ecgs": {key: len(value) for key, value in selections.items()},
              "feature_cache_sha256": digest(array_path), "runs": {}, "baseline_score_diagnostics": {}}
    metrics = []
    for profile in ("P6", "P8"):
        path = linear_dir / f"{profile}.npz"
        if digest(path) != line["profiles"][profile]["sha256"]:
            raise ValueError("linear comparator changed")
        with np.load(path, allow_pickle=False) as linear, np.load(array_path, allow_pickle=False) as arrays:
            mean, scale = linear["mean"], linear["scale"]
            datasets = {key: load_split(arrays, rows, profile, columns, ids, mean, scale)
                        for key, ids in selections.items()}
            raw, x, old, links, labels, cohort = datasets["descriptive"]
            old_scores = aggregate(old, links, len(labels), profile)
            shift = {}
            for split, (_, _, base, indices, target, records) in datasets.items():
                probability = aggregate(base, indices, len(target), profile)
                sources = np.asarray([row["source"] for row in records])
                for source in np.unique(sources):
                    for j, endpoint in enumerate(endpoints):
                        for polarity, polarity_name in ((0, "negative"), (1, "positive")):
                            values = probability[(sources == source) & (target[:, j] == polarity), j]
                            shift[f"{split}/{source}/{endpoint}/{polarity_name}"] = {
                                "n_ecg": len(values), "median": float(np.median(values)) if len(values) >= 10 else None,
                            }
            report["baseline_score_diagnostics"][profile] = shift
            all_scores = {"anchored_linear_residual_v1": aggregate(residual_logits(
                raw, old, mean, scale, linear["coefficients"], linear["cap"]
            ), links, len(labels), profile)}
            report["runs"][profile] = {}
            for name, gamma in config["variants"].items():
                model, info = fit_variant(datasets["train"], datasets["validation"], profile, config, gamma)
                ckpt = output / f"{profile}-{name}.pt"
                torch.save(model.state_dict(), ckpt)
                report["runs"][profile][name] = {**info, "checkpoint_sha256": digest(ckpt)}
                with torch.no_grad():
                    z = old + config["residual_cap"] * model(torch.from_numpy(x)).tanh().numpy()
                all_scores[name] = aggregate(z, links, len(labels), profile)
            thresholds = np.array([metadata["baseline_thresholds"][profile][name] for name in endpoints])
            for name, scores in all_scores.items():
                result, comparison = paired_metrics(
                    labels, old_scores, scores, np.array([row["identity_hash"] for row in cohort]),
                    thresholds, endpoints, protocol["evaluation"],
                )
                report["runs"][profile].setdefault(name, {})["georgia_descriptive"] = comparison
                for item in result:
                    metrics.append({"profile": profile, "variant": name, "source": "georgia",
                                    "bootstrap_unit": "ecg_record_not_patient", **item})
    table = output / "SPECIALIST_IMPROVEMENT_EXPERIMENTS.csv"
    with table.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(metrics[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(metrics)
    report["aggregate_csv_sha256"] = digest(table)
    report["promotion"] = "NOT_ASSESSED_DEVELOPMENT_ONLY"
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    (output / "development_ablation_receipt.json").write_bytes(text.encode())
    print(text, end="")


if __name__ == "__main__":
    os.umask(0o077)
    cli = argparse.ArgumentParser(description=__doc__)
    for name in ("feature_dir", "linear_dir", "output"):
        cli.add_argument(name, type=Path)
    run(**vars(cli.parse_args()))
