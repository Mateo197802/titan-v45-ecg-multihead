"""Score frozen candidate checkpoints across development sources, never CODE test."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch
from evaluate_new_holdout import candidate_scores, measure, write_csv
from train_duration_aware import (
    PROTOCOL,
    TemporalSpecialist,
    digest,
    read_bank,
    read_extra,
    write_json,
)

from titan_v45.models.factory import build_titan_v45_backbone


def run(code, extra, out, runs):
    cfg = json.loads(PROTOCOL.read_bytes())
    out.mkdir(mode=0o700, exist_ok=False)
    rows, inputs, cache = [], {}, {}
    source_key = {"chapman_only_partial": "chapman_shaoxing", "multisource_groupdro": "code15|chapman_shaoxing|cpsc2018"}
    for run in runs:
        path, checkpoint = run / "TRAINING_RECEIPT.json", run / "best.pt"
        receipt = json.loads(path.read_bytes())
        if (receipt["protocol_sha256"] != digest(PROTOCOL) or receipt["calibration_or_test_opened"]
                or receipt["checkpoint_sha256"] != digest(checkpoint)
                or receipt["bank_receipt_sha256"] != digest(code / "CODE_DEVELOPMENT_RECEIPT.json")):
            raise ValueError("checkpoint or development-bank seal mismatch")
        mode, norm = receipt["mode"], receipt["normalization"]
        state = torch.load(checkpoint, map_location="cpu", weights_only=True)
        model = TemporalSpecialist(build_titan_v45_backbone())
        model.load_state_dict(state["state_dict"], strict=True)
        model.cuda().eval()
        sources = source_key.get(mode, "code15")
        for source in ("code15", "chapman_shaoxing"):
            key = source, norm
            if key not in cache:
                cache[key] = (read_bank(code, "validation", norm) if source == "code15"
                              else read_extra(extra, source, "validation", norm))
            probabilities, _, patients, labels = candidate_scores(model, cache[key], cfg["training"]["batch_size"])
            for index, endpoint in enumerate(cfg["endpoints"]):
                keep = labels[:, index] >= 0
                truth, p = labels[keep, index], probabilities[keep, index]
                estimable = len(np.unique(truth)) == 2
                metric = measure(truth, p, .5) if estimable else dict.fromkeys(
                    ("tp", "tn", "fp", "fn", "specificity", "f1", "auroc", "ece", "sensitivity", "ppv", "npv", "auprc", "brier"))
                rows.append({"mode": mode, "seed": receipt["seed"], "normalization": norm,
                             "supervised_training_sources": sources, "scored_source": source,
                             "source_absent_from_new_supervised_fit": source not in sources.split("|"),
                             "scope": "HISTORICALLY_EXPOSED_DEVELOPMENT_SOURCE", "endpoint": endpoint,
                             "ecgs": len(truth), "patients": len(set(patients[keep])),
                             "positive_ecgs": int(truth.sum()), "estimable": estimable, **metric})
        inputs[receipt["checkpoint_sha256"]] = digest(path)
        del model, state
    target = out / "SOURCE_GENERALIZATION_MATRIX.csv"
    write_csv(target, rows)
    write_json(out / "SOURCE_GENERALIZATION_RECEIPT.json", {"rows": len(rows), "metrics_sha256": digest(target),
               "checkpoint_to_training_receipt_sha256": inputs, "protocol_sha256": digest(PROTOCOL),
               "code_evaluation_test_opened": False, "independent_generalization": "NOT_EVALUATED"})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("code", "extra", "output"):
        parser.add_argument(name, type=Path)
    parser.add_argument("runs", type=Path, nargs="+")
    args = parser.parse_args()
    run(args.code, args.extra, args.output, args.runs)
