"""Select architecture and checkpoint using only versioned validation receipts."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import mean, pstdev

from build_code_development import PROTOCOL, ROOT, digest, write_json

SELECTION = ROOT / "docs/domain_adaptation/SELECTION_PROTOCOL.json"


def variant(row):
    return row["mode"], row["normalization"]


def initial_finalists(rows, policy, initial_seed):
    initial = [row for row in rows if row["seed"] == initial_seed]
    frozen = [r for r in initial if r["mode"] == "frozen_backbone_mlp"]
    nonfrozen = [r for r in initial if r["mode"] in policy["eligible_nonfrozen"]]
    if not frozen or not nonfrozen:
        raise ValueError("require a completed frozen and nonfrozen development fit")
    return [variant(min(group, key=lambda r: (-r["validation_macro_ap"], *variant(r))))
            for group in (frozen, nonfrozen)]


def choose(rows, policy, seeds):
    finalists = initial_finalists(rows, policy, seeds[0])
    results = []
    for mode, norm in finalists:
        group = [r for r in rows if variant(r) == (mode, norm)]
        if sorted(r["seed"] for r in group) != sorted(seeds):
            raise ValueError(f"finalist seed coverage incomplete: {mode}/{norm}")
        scores = [r["validation_macro_ap"] for r in group]
        results.append({"mode": mode, "normalization": norm, "mean_macro_ap": mean(scores),
                        "sd_macro_ap_population": pstdev(scores),
                        "mean_macro_f1_at_half": mean(r["validation_macro_f1_at_half"] for r in group),
                        "sd_macro_f1_at_half_population": pstdev(r["validation_macro_f1_at_half"] for r in group),
                        "seeds": [{k: r[k] for k in ("seed", "validation_macro_ap", "validation_macro_f1_at_half",
                                                     "checkpoint_sha256", "slurm_job")} for r in sorted(group, key=lambda r: r["seed"])]})
    best = min(results, key=lambda r: (-r["mean_macro_ap"], r["mode"] != "frozen_backbone_mlp", *variant(r)))
    group = sorted((r for r in rows if variant(r) == variant(best)), key=lambda r: (r["validation_macro_ap"], r["seed"]))
    return group[len(group) // 2], results


def load_validation_rows(bank, run_dirs):
    rows, seen = [], set()
    bank_hash = digest(bank / "CODE_DEVELOPMENT_RECEIPT.json")
    for folder in run_dirs:
        path = folder / "TRAINING_RECEIPT.json"
        row = json.loads(path.read_bytes())
        key = (*variant(row), row["seed"])
        if (row["protocol_sha256"] != digest(PROTOCOL) or row["bank_receipt_sha256"] != bank_hash
                or row["calibration_or_test_opened"] or row.get("validation_source", "code15") != "code15"
                or any(not math.isfinite(row[m]) or not 0 <= row[m] <= 1
                       for m in ("validation_macro_ap", "validation_macro_f1_at_half"))
                or digest(folder / "best.pt") != row["checkpoint_sha256"]
                or digest(folder / "FINETUNING_LEARNING_CURVES.csv") != row["curves_sha256"] or key in seen):
            raise ValueError("fit not comparable, duplicated, or altered")
        seen.add(key)
        rows.append({**row, "receipt_sha256": digest(path)})
    return rows


def run(bank, output, run_dirs, shortlist):
    cfg = json.loads(PROTOCOL.read_bytes())
    policy = json.loads(SELECTION.read_bytes())
    if policy["parent_protocol_sha256"] != digest(PROTOCOL):
        raise ValueError("selection policy is not linked to the parent protocol")
    rows = load_validation_rows(bank, run_dirs)
    seeds = cfg["training"]["seeds"]
    result = {"protocol_sha256": digest(PROTOCOL), "selection_protocol_sha256": digest(SELECTION),
              "selection_source": "validation_only", "shortlist": initial_finalists(rows, policy, seeds[0]),
              "considered_runs": sorted((row["slurm_job"], row["receipt_sha256"]) for row in rows)}
    if not shortlist:
        selected, finalists = choose(rows, policy, seeds)
        result.update(selected_checkpoint_sha256=selected["checkpoint_sha256"],
                      selected_training_receipt_sha256=selected["receipt_sha256"],
                      selected_seed=selected["seed"], selected_mode=selected["mode"],
                      selected_normalization=selected["normalization"], finalists=finalists)
    write_json(output, result)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bank", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("run_dirs", type=Path, nargs="+")
    parser.add_argument("--shortlist", action="store_true")
    args = parser.parse_args()
    run(args.bank, args.output, args.run_dirs, args.shortlist)
