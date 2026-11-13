"""Replay frozen development predictions and obtain direct MLP-minus-linear intervals."""
from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path

import numpy as np
import torch
from code15_io import PROTOCOL, digest
from evaluate_code15 import paired_metrics
from fit_code_transfer import P8_CLASSES, residual_logits
from run_development_ablation import FREEZE, aggregate, load_split
from torch import nn


def run(feature_dir, linear_dir, ablation_dir, out):
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    cfg = json.loads(FREEZE.read_bytes())
    protocol = json.loads(PROTOCOL.read_bytes())
    history = json.loads((ablation_dir / "development_ablation_receipt.json").read_bytes())
    table = ablation_dir / "SPECIALIST_IMPROVEMENT_EXPERIMENTS.csv"
    path = feature_dir / "private_frozen_features.npz"
    if (history["protocol_sha256"] != digest(FREEZE) or history["feature_cache_sha256"] != digest(path)
            or history["aggregate_csv_sha256"] != digest(table)
            or history["code15_inputs_opened"] or history["mimic_inputs_opened"]):
        raise ValueError("development provenance mismatch")
    linear_receipt = json.loads((linear_dir / "candidate_receipt.json").read_bytes())
    metadata = json.loads((feature_dir / "private_feature_metadata.json").read_bytes())
    endpoints = cfg["classes"]
    columns = [P8_CLASSES.index(name) for name in endpoints]
    rows = metadata["rhythm_records"]
    ids = [i for i, row in enumerate(rows) if row["scored"] and row["split"] == cfg["descriptive_split"]
           and row["source"] == cfg["descriptive_source"]]
    with table.open(encoding="utf-8", newline="") as stream:
        originals = {(r["profile"], r["variant"], r["endpoint"], r["model"]): r for r in csv.DictReader(stream)}
    result = {"input_aggregate_sha256": digest(table), "development_only": True,
              "bootstrap_unit": "ecg_record_not_patient", "contrasts_mlp_minus_linear": {},
              "verified_original_rows": 0}
    private = {}
    for profile, runs in history["runs"].items():
        linear_path = linear_dir / f"{profile}.npz"
        if digest(linear_path) != linear_receipt["profiles"][profile]["sha256"]:
            raise ValueError("sealed linear checkpoint changed")
        with np.load(linear_path, allow_pickle=False) as linear, np.load(path, allow_pickle=False) as arrays:
            mean, scale = linear["mean"], linear["scale"]
            raw, x, old, links, labels, records = load_split(arrays, rows, profile, columns, ids, mean, scale)
            published = aggregate(old, links, len(labels), profile)
            linear_scores = aggregate(residual_logits(raw, old, mean, scale, linear["coefficients"],
                                                       linear["cap"]), links, len(labels), profile)
        thresholds = np.array([metadata["baseline_thresholds"][profile][name] for name in endpoints])
        groups = np.array([row["identity_hash"] for row in records])
        result["contrasts_mlp_minus_linear"][profile] = {}
        private.update({profile + "_published": published, profile + "_linear": linear_scores})
        for name, run_receipt in runs.items():
            if name == "anchored_linear_residual_v1":
                scores = linear_scores
            else:
                checkpoint = ablation_dir / f"{profile}-{name}.pt"
                if digest(checkpoint) != run_receipt["checkpoint_sha256"]:
                    raise ValueError("sealed MLP checkpoint changed")
                model = nn.Sequential(nn.Linear(x.shape[1], cfg["hidden_width"]), nn.SiLU(),
                                      nn.Dropout(cfg["dropout"]), nn.Linear(cfg["hidden_width"], len(endpoints)))
                model.load_state_dict(torch.load(checkpoint, map_location="cpu", weights_only=True))
                model.eval()
                with torch.no_grad():
                    z = old + cfg["residual_cap"] * model(torch.from_numpy(x)).tanh().numpy()
                scores = aggregate(z, links, len(labels), profile)
                private[f"{profile}_{name}"] = scores
                _, contrast = paired_metrics(labels, linear_scores, scores, groups, thresholds, endpoints,
                                             protocol["evaluation"])
                result["contrasts_mlp_minus_linear"][profile][name] = contrast
            expected, comparison = paired_metrics(labels, published, scores, groups, thresholds, endpoints,
                                                   protocol["evaluation"])
            if comparison != run_receipt["georgia_descriptive"]:
                raise ValueError("replayed summary differs")
            for row in expected:
                original = originals[profile, name, row["endpoint"], row["model"]]
                if any(original[key] != ("" if value is None else str(value)) for key, value in row.items()):
                    raise ValueError("replayed per-class row differs")
                result["verified_original_rows"] += 1
    out.mkdir(mode=0o700, exist_ok=False)
    predictions = out / "private_georgia_replayed.npz"
    np.savez_compressed(predictions, labels=labels, groups=groups, **private)
    result["private_predictions_sha256"] = digest(predictions)
    text = json.dumps(result, sort_keys=True, indent=2) + "\n"
    (out / "development_ablation_replay.json").write_bytes(text.encode())
    print(text, end="")


if __name__ == "__main__":
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("feature_dir", "linear_dir", "ablation_dir", "out"):
        parser.add_argument(name, type=Path)
    run(**vars(parser.parse_args()))
