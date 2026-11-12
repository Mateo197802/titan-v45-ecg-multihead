"""New paired nonlinear-head ablation, not a replay of published training."""
import argparse
import json
import os
import time
from pathlib import Path

import numpy as np
import torch
from compare_reviewer_baseline import digest
from reviewer_morphology_retrained import (
    ARMS,
    load_features,
    paired_macro,
    polarity,
    select_profiles,
    selected,
    threshold,
)
from scipy.special import expit
from score_reviewer_closure_ludb import write_new

from titan_v45.evaluation.revision_report import binary_metrics

FEATURE_RECEIPT = "de65d38ef6c3c00cae2546858924ab87a7656e754fe4a52aaac7a2d7b328f3cb"
INVENTORY = "798866dc1dc00d3e81c9fda28711dd0ea57fb57a7fc2ac0a415ad20a97f17107"


def window_index(wi, records):
    select = np.isin(wi, records)
    index = np.searchsorted(records, wi[select])
    counts = np.bincount(index, minlength=len(records))
    if not len(counts) or np.any(counts == 0):
        raise ValueError("scored ECG missing from feature windows")
    return select, index, counts


def fit_arm(x, wi, ids, y, seed, recipe):
    sel, index, counts = window_index(wi, ids)
    values = x[sel]
    weights = 1 / counts[index]
    mean = np.average(values, weights=weights, axis=0)
    scale = np.maximum(np.average((values-mean)**2, weights=weights, axis=0)**0.5, 1e-5)
    features = torch.from_numpy(((values-mean)/scale).astype(np.float32))
    labels = torch.from_numpy(y[index].astype(np.float32))
    weight = torch.from_numpy((weights/weights.mean()).astype(np.float32))
    torch.manual_seed(seed)
    model = torch.nn.Sequential(torch.nn.Linear(x.shape[1], 32), torch.nn.ReLU(), torch.nn.Linear(32, 1))
    optimizer = torch.optim.SGD(model.parameters(), lr=recipe["learning_rate"], weight_decay=recipe["weight_decay"])
    schedule = np.random.default_rng(seed)
    losses = []
    for _ in range(recipe["epochs"]):
        running = 0.0
        for batch in np.array_split(schedule.permutation(len(values)),
                                    (len(values) + recipe["batch_size"] - 1)//recipe["batch_size"]):
            optimizer.zero_grad()
            logit = model(features[batch]).flatten()
            loss = torch.nn.functional.binary_cross_entropy_with_logits(logit, labels[batch], weight=weight[batch])
            loss.backward()
            optimizer.step()
            running += float(loss.detach())*len(batch)
        losses.append(running/len(values))
    if not np.isfinite(losses).all():
        raise ValueError("nonfinite training loss")
    return model.eval(), mean, scale, losses


def scores(fit, x, wi, records, profile):
    model, mean, scale, _ = fit
    sel, index, counts = window_index(wi, records)
    with torch.inference_mode():
        z = model(torch.from_numpy(((x[sel]-mean)/scale).astype(np.float32))).flatten().numpy()
    if not np.isfinite(z).all():
        raise ValueError("nonfinite model logits")
    result = np.bincount(index, weights=z if profile == "P6" else expit(z), minlength=len(counts))/counts
    return expit(result) if profile == "P6" else result


def run(protocol, original, profiles, private):
    recipe = protocol["morphology"]
    requirement = original["training"]
    results = {}
    for p, rows, wi, labels, columns, xs, splits, counts in profiles:
        print(f"Starting {p}", flush=True)
        times, endpoints, all_trials, by_seed = [], {}, [], {s: [] for s in recipe["seeds"]}
        for label, col in zip(labels, columns, strict=True):
            train, cal, test = (selected(rows, splits, name, col) for name in ("train", "calibration", "held"))
            ty, cy, ey = (np.asarray([rows[i]["targets"][col] for i in ids], dtype=np.int8)
                          for ids in (train, cal, test))
            support = {name: {"positive": int(y.sum()), "negative": int(len(y)-y.sum())}
                       for name, y in zip(("train", "calibration", "held"), (ty, cy, ey), strict=True)}
            endpoint = {"support": support, "status": "insufficient_common_support"}
            endpoints[label] = endpoint
            if (polarity(ty) < requirement["minimum_training_records_per_polarity"]
                    or polarity(cy) < requirement["minimum_calibration_records_per_polarity"] or polarity(ey) == 0):
                continue
            endpoint.update(status="evaluated", seeds={})
            for seed in recipe["seeds"]:
                predictions, metrics = {}, {}
                for arm in ARMS:
                    start = time.perf_counter()
                    fitted = fit_arm(xs[arm], wi, train, ty, seed, recipe)
                    elapsed = time.perf_counter() - start
                    times.append(elapsed)
                    bound = threshold(cy, scores(fitted, xs[arm], wi, cal, p))
                    probability = scores(fitted, xs[arm], wi, test, p)
                    predictions[arm] = (probability >= bound).astype(np.int8)
                    metrics[arm] = {"threshold": bound, "train_seconds": elapsed,
                                    "parameters": sum(t.numel() for t in fitted[0].parameters()),
                                    "train_loss_first_last": [fitted[3][0], fitted[3][-1]],
                                    **binary_metrics(ey, predictions[arm], probability)}
                    private.write(json.dumps({"profile": p, "class": label, "seed": seed, "arm": arm,
                                              "records": [rows[i]["identity_hash"] for i in test],
                                              "reference": ey.tolist(), "scores": probability.tolist(),
                                              "decisions": predictions[arm].tolist()}, allow_nan=False)+"\n")
                endpoint["seeds"][seed] = metrics
                by_seed[seed].append([metrics[arm]["f1"] for arm in ARMS])
                all_trials.append((test, ey, *(predictions[arm] for arm in ARMS)))
        contrast = paired_macro(all_trials, [r["group_hash"] for r in rows],
                                {"seed": recipe["bootstrap_seed"], "replicates": recipe["replicates"],
                                 "level": 1 - 0.05/len(original["profiles"])})
        bounds = contrast["bounds"] if contrast else None
        if contrast:
            contrast["full_interval_width"] = bounds[1]-bounds[0] if bounds else None
            contrast["precision_adequate_for_margin_classification"] = (
                contrast["valid_replicates"] >= 0.95 * recipe["replicates"])
            margin = recipe["effect_margin_macro_f1"]
            status = "inconclusive"
            if bounds and contrast["precision_adequate_for_margin_classification"]:
                if bounds[0] > margin:
                    status = "benefit_above_margin"
                elif bounds[1] < -margin:
                    status = "harm_beyond_margin"
                elif bounds[0] > -margin and bounds[1] < margin:
                    status = "effects_within_prespecified_margin"
            contrast["classification"] = status
        results[p] = {"split_record_counts": counts, "group_and_exact_signal_overlap": False,
                      "grouping": "official PTB-XL patient" if p == "P4" else "Chapman record proxy, not verified patient ID",
                      "feature_width": xs[ARMS[0]].shape[1], "training_seconds": sum(times), "contrast": contrast,
                      "seed_macro_f1": {s: dict(zip(ARMS, np.mean(v, axis=0).tolist(), strict=True)) if v else None
                                        for s, v in by_seed.items()},
                      "endpoints": endpoints}
        print(f"Finished {p}; paired contrast={contrast}", flush=True)
    return results


def main():
    p = argparse.ArgumentParser()
    for key in ("protocol", "original", "features", "inventory", "output"):
        p.add_argument(f"--{key}", type=Path, required=True)
    a = p.parse_args()
    protocol = json.loads(a.protocol.read_bytes())
    if digest(a.inventory) != INVENTORY or digest(a.features / "extraction-receipt.json") != FEATURE_RECEIPT:
        raise ValueError("prespecified source seal differs")
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    original, arrays, meta, signals, receipt = load_features(a.original, a.features, a.inventory)
    private = a.output.with_name("private-ablation-predictions.jsonl")
    with private.open("x", encoding="utf-8") as f:
        result = run(protocol, original, select_profiles(original, arrays, meta, signals), f)
    write_new(a.output, {"job": os.environ.get("SLURM_JOB_ID"), "design": protocol["design"],
                         "scope": protocol["morphology"]["scope"], "seeds": protocol["morphology"]["seeds"],
                         "protocol_sha256": digest(a.protocol), "original_protocol_sha256": digest(a.original),
                         "feature_receipt_sha256": receipt, "inventory_sha256": INVENTORY,
                         "private_predictions_sha256": digest(private), "individual_data_exported": False,
                         "torch": str(torch.__version__), "device": "cpu", "profiles": result})


if __name__ == "__main__":
    main()
