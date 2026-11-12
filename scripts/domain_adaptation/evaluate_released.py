"""Evaluate the original P6/P8 heads on the corrected validation waveforms."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import torch
from train_duration_aware import PROTOCOL, ROOT, batches, digest, read_bank, write_json

sys.path.insert(0, str(ROOT / "scripts/specialist_experiments"))
from extract_features import _baseline_thresholds, _safe_morphology

from titan_v45.evaluation.revision_report import binary_metrics
from titan_v45.models.frozen_pathology import verified_assets
from titan_v45.models.frozen_rhythm import (
    BACKBONE,
    HEADS,
    P8_CLASSES,
    FrozenRhythm,
    load_recorded_event_extractor,
)


def load_released(assets):
    paths, hashes = verified_assets(ROOT, assets, {BACKBONE, *HEADS.values()})
    old = json.loads((ROOT / "docs/external_validation_20261111/FROZEN_EXTERNAL_EVALUATION_PROTOCOL.json").read_bytes())
    if hashes != {name: old["baseline"][name] for name in paths}:
        raise ValueError("released P6/P8 assets differ from PR #6")
    contract = json.loads((ROOT / "outputs/models/heads/global_head_contracts.json").read_bytes())
    source = ROOT / "docs/provenance/recovered-original-sources-20261029.zip"
    model = FrozenRhythm(paths, contract, load_recorded_event_extractor(source), "cuda")
    thresholds = _baseline_thresholds(ROOT, SimpleNamespace(thresholds={}))
    return model, thresholds, hashes


def score_released(model, data, batch_size, endpoints):
    morphology = _safe_morphology(ROOT)
    columns = [P8_CLASSES.index(name) for name in endpoints]
    outputs, y, exams, patients, durations = defaultdict(list), [], [], [], []
    for wave, _, labels, _, ids, person in batches(data, batch_size):
        samples = [(x, np.ones(12, dtype=bool), morphology(x, fs=125)) for x in wave]
        raw, _ = model(samples)
        for profile, logits in raw.items():
            if profile == "P6":
                score = 1 / (1 + np.exp(-np.clip(logits[:, columns].astype(np.float64), -50, 50)))
            else:
                score = torch.as_tensor(logits[:, columns], dtype=torch.float32).sigmoid().numpy()
            outputs[profile].append(score)
        y.append(labels)
        exams.append(ids)
        patients.append(person)
        durations.extend([wave.shape[-1]] * len(wave))
    return ({key: np.concatenate(value) for key, value in outputs.items()}, np.concatenate(y),
            np.concatenate(exams), np.concatenate(patients), np.asarray(durations))


def run(bank, assets, out):
    cfg = json.loads(PROTOCOL.read_bytes())
    endpoints = list(cfg["endpoints"])
    model, thresholds, hashes = load_released(assets)
    out.mkdir(mode=0o700, exist_ok=False)
    rows = []
    for mode in cfg["waveform"]["normalizations"]:
        data = read_bank(bank, "validation", mode)
        scores, labels, exams, patients, durations = score_released(model, data, cfg["training"]["batch_size"], endpoints)
        for profile, matrix in scores.items():
            for name, mask in (("all", np.ones(len(exams), bool)), ("short_7p335", durations == 917),
                               ("long_10", durations == 1250)):
                for i, endpoint in enumerate(endpoints):
                    keep = mask & (labels[:, i] >= 0)
                    y, p = labels[keep, i].astype(int), matrix[keep, i]
                    if not len(y):
                        continue
                    result = binary_metrics(y, p >= thresholds[profile][endpoint], p)
                    rows.append({"source": "code15", "split": "validation", "duration": name, "profile": profile,
                                 "normalization": mode, "endpoint": endpoint, "threshold": thresholds[profile][endpoint],
                                 "patients": len(set(patients[keep])), **result})
        np.savez_compressed(out / f"private_validation_{mode}.npz", exams=exams, patients=patients,
                            labels=labels, durations=durations, **scores)
    csv_path = out / "SIGNAL_PROCESSING_ABLATIONS.csv"
    with csv_path.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    receipt = {"scope": "CODE_VALIDATION_CORRECTED_WAVEFORMS_ONLY", "assets": hashes,
               "rows": len(rows), "protocol_sha256": digest(PROTOCOL), "metrics_sha256": digest(csv_path),
               "test_opened": False, "historical_benchmark_changed": False}
    write_json(out / "VALIDATION_BASELINES_RECEIPT.json", receipt)
    print(json.dumps(receipt, sort_keys=True), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("bank", "assets", "output"):
        parser.add_argument(key, type=Path)
    args = parser.parse_args()
    run(args.bank, args.assets, args.output)
