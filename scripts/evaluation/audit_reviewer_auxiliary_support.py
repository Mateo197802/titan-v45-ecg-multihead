"""Audit observed reference support and rank released, mapped auxiliary scores."""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
from collections import Counter
from pathlib import Path

from compare_reviewer_baseline import digest, load_ledger


def reference(codes, targets, normal):
    if normal in codes and len(codes) != 1:
        return "ambiguous"
    if targets & codes:
        return "positive"
    if codes == {normal}:
        return "explicit_normal_control"
    return "unknown"


def rank_metrics(pairs):
    score_groups = {}
    for score, positive in pairs:
        if not math.isfinite(score):
            raise ValueError("nonfinite auxiliary score")
        bucket = score_groups.setdefault(score, [0, 0])
        bucket[int(positive)] += 1
    p = sum(pos for _, pos in score_groups.values())
    n = sum(neg for neg, _ in score_groups.values())
    if not p or not n:
        return {"positive": p, "explicit_normal_control": n, "auroc": None, "average_precision": None}
    tp = fp = ap = wins = 0
    for _, (neg, pos) in sorted(score_groups.items(), reverse=True):
        wins += pos * (n - fp - neg / 2)
        tp += pos
        fp += neg
        ap += pos / p * tp / (tp + fp)
    return {"positive": p, "explicit_normal_control": n,
            "auroc": wins / (p * n), "average_precision": ap}


def main():
    from titan_v45.data.sph import read_sph_dictionary, read_sph_metadata

    p = argparse.ArgumentParser(description=__doc__)
    for name in ("phase", "ontology", "source", "ledger", "receipt", "output"):
        p.add_argument(f"--{name}", type=Path, required=True)
    a = p.parse_args()
    phase, ont = json.loads(a.phase.read_bytes()), json.loads(a.ontology.read_bytes())
    rows, meta = load_ledger(a.ledger, a.receipt, phase)
    for n in ("metadata.csv", "code.csv"):
        if digest(a.source/n) != meta["source_sha256"][n]:
            raise ValueError("SPH input digest mismatch")
    dictionary = (a.source/"code.csv").read_text(encoding="utf-8-sig")
    codes = {int(r["Code"]): r["Description"] for r in csv.DictReader(dictionary.splitlines())}
    for spec in [ont["normal"], *ont["endpoints"]]:
        if codes.get(spec["code"]) != spec["description"]:
            raise ValueError("ontology description differs from source dictionary")
    primary, modifier = read_sph_dictionary(dictionary)
    metadata = read_sph_metadata((a.source/"metadata.csv").read_text(encoding="utf-8-sig"), primary, modifier)
    if rows.keys() != metadata.keys():
        raise ValueError("ledger and reference populations differ")
    normal = ont["normal"]["code"]
    reports = {}
    for e in ont["endpoints"]:
        support, flow, ranking = Counter(), Counter(), []
        for key, row in rows.items():
            ref = reference(metadata[key].primary_codes, {e["code"]}, normal)
            support[ref] += 1
            flow[f'{ref}:{row["status"]}'] += 1
            if row["status"] == "scored" and ref in {"positive", "explicit_normal_control"}:
                score = row["profiles"][e["profile"]]["auxiliary_scores"][e["score_key"]]
                ranking.append((score, ref == "positive"))
        reports[e["name"]] = {
            "mapping": e, "all_source_reference_states": dict(support),
            "reference_by_scoring_state": dict(flow), "ranking_known_statement_subset": rank_metrics(ranking),
        }
    other = {}
    for name, targets in ont["other_support_screen"].items():
        if not isinstance(targets, list):
            continue
        other[name] = dict(Counter(reference(r.primary_codes, set(targets), normal)
                                   for r in metadata.values()))
    output = {
        "job": os.environ.get("SLURM_JOB_ID"), "scope": ont["scope"],
        "source_ecgs": len(metadata), "scored_flow": meta["flow"],
        "ontology_sha256": digest(a.ontology), "baseline_receipt_sha256": digest(a.receipt),
        "endpoints": reports, "observable_other_support_only": other,
        "unknown_auxiliary_reference": ont["declared_auxiliary_without_validated_mapping"],
        "normal_code": ont["normal"], "record_identifiers_exported": False,
        "other_classifier_validated": False, "auxiliary_training_inferred_from_scores": False,
    }
    with a.output.open("x", encoding="utf-8") as f:
        json.dump(output, f, allow_nan=False, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
