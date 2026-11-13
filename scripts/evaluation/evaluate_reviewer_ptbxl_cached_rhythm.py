"""Evaluate new V3AG rhythm readouts from sealed Stage A features, not waveforms.

Protocol: score every cached ECG; compare reconstructed softmax columns with
the archived primary-eight columns before joining references. Fit only a
Youden operating point on folds 1-8, with exact-score ties grouped and the
highest maximizing threshold preferred. Hold fold 9; fold 10 stays locked.
Pooled ranks are descriptive. No backbone, head, or published threshold is
changed, and no result is historically independent or clinically adjudicated.
"""
from __future__ import annotations

import argparse
import ast
import csv
import json
import os
from collections import Counter
from pathlib import Path

import numpy as np
from audit_reviewer_ptbxl_other_support import SOURCE_SHA, digest, disposition, identity
from score_reviewer_closure_ludb import write_new

ENDPOINTS = ("Paced", "2AVB", "3AVB")
ARCHIVED_ORDER = ("AFIB", "SB", "STACH", "NSR", "RBBB", "PAC", "1AVB", "PVC")
POSITIVE = "positive"
NEGATIVE = "explicit_normal_control"
MIN_GROUPS = 5
DESIGN = {"seed": 197841, "n_bootstrap": 2000, "confidence": 0.95}
FEATURE_META_SHA = "c3a5e7a7d3d08c92fb1e2d7175a8fe1d87ebfb3df51f530ba7929bc66b185321"
CACHE_SHA = "9269716a656211fbe81e3ede45b0ea09eaa2437442db8dd2a25fd4006c36592a"
BACKBONE_SHA = "bf71e4cf8acc34031cb3611c7031e0649822e705fd7dcea354a3ea583ce920ee"
SUPPORT_SHA = "1e758fcb0cc17e7cc15ff8be2fcb7911a6f102d4dd5d673cec440d409a187bcd"


def cutoff(y, p):
    order = np.argsort(-p, kind="stable")
    ends = np.r_[np.flatnonzero(np.diff(p[order])), len(p) - 1]
    tp = np.cumsum(y[order])[ends]
    fp = (ends + 1) - tp
    pos, neg = int(y.sum()), len(y) - int(y.sum())
    if not pos or not neg:
        raise ValueError("calibration needs two reference polarities")
    objective = np.r_[0, tp * neg - fp * pos]
    thresholds = np.r_[np.nextafter(p[order[0]], np.inf), p[order[ends]]]
    return float(thresholds[int(np.argmax(objective))])


def sufficient(info):
    return min(info["positive_subjects"], info["control_subjects"]) >= MIN_GROUPS


def sample(rows, predicate):
    subset = [r for r in rows if predicate(r[0])]
    selected = [r for r in subset if r[2] in (POSITIVE, NEGATIVE)]
    g = np.asarray([r[1] for r in selected])
    y = np.asarray([r[2] == POSITIVE for r in selected], dtype=int)
    p = np.asarray([r[3] for r in selected], dtype=float)
    info = {"eligible_cache_ecgs": len(subset), "reference_states": Counter(r[2] for r in subset),
            "positive_subjects": len(set(g[y == 1])), "control_subjects": len(set(g[y == 0]))}
    return info, y, p, g


def score(args, records, matrix):
    import torch

    from titan_v45.models.factory import build_titan_v45_backbone
    from titan_v45.models.features import recovered_backbone_rhythm_probabilities
    from titan_v45.models.frozen_pathology import BACKBONE, SPECIALIST, verified_assets

    assets, hashes = verified_assets(args.repo, args.assets, {BACKBONE, SPECIALIST})
    if hashes[BACKBONE] != BACKBONE_SHA:
        raise ValueError("released V3AG weights differ")
    classes = json.loads((args.repo / "outputs/models/heads/global_head_contracts.json").read_bytes())[
        "heads"]["rhythm"]["classes"]
    checkpoint = torch.load(assets[SPECIALIST], map_location="cpu", weights_only=True)
    stored = tuple(checkpoint["primary8_classes"]) + tuple(checkpoint["specialist_rhythm_classes"])
    if tuple(classes[:8]) != ARCHIVED_ORDER or len(stored) != 16 or len(set(classes)) != 14:
        raise ValueError("unsupported Stage A rhythm layout")
    state = torch.load(assets[BACKBONE], map_location="cpu", weights_only=True)["state_dict"]
    head = build_titan_v45_backbone().head_rhythm.eval()
    head.load_state_dict({k.removeprefix("head_rhythm."): v for k, v in state.items()
                          if k.startswith("head_rhythm.")}, strict=True)
    with torch.inference_mode():
        scores = torch.cat([recovered_backbone_rhythm_probabilities(
            head(torch.from_numpy(np.ascontiguousarray(block[:, :650]))))
            for block in np.array_split(matrix, 32)]).numpy()
    error = float(np.max(np.abs(scores[:, [classes.index(k) for k in stored]] - matrix[:, 650:666])))
    if not np.isfinite(scores).all() or error > 1e-5:
        raise ValueError("V3AG cached readout does not reproduce archived P4 rhythm columns")
    write_new(args.output / "private-readout.json", [
        {"key": r["identity_hash"], "scores": dict(zip(ENDPOINTS, map(float, s), strict=True))}
        for r, s in zip(records, scores[:, [classes.index(k) for k in ENDPOINTS]], strict=True)])
    write_new(args.output / "scoring-receipt.json", {
        "job": os.environ.get("SLURM_JOB_ID"), "scored": len(records), "asset_sha256": hashes,
        "cached_features_sha256": CACHE_SHA, "feature_metadata_sha256": FEATURE_META_SHA,
        "private_score_sha256": digest(args.output / "private-readout.json"),
        "archived_probability_columns_checked": 16, "max_absolute_archived_score_error": error,
        "source_reference_values_used": False, "waveform_inference": False, "native_runtime": torch.__version__,
    })


def evaluate(args, records):
    from titan_v45.evaluation.specialist_heads import bootstrap_binary_metrics

    from titan_v45.evaluation.revision_report import binary_metrics

    receipt = args.output / "scoring-receipt.json"
    check = json.loads(receipt.read_bytes())
    private = args.output / "private-readout.json"
    if (digest(receipt) != args.score_receipt_sha256 or digest(private) != check["private_score_sha256"]
            or check["source_reference_values_used"] is not False):
        raise ValueError("readout must be sealed before joining source labels")
    scores = json.loads(private.read_bytes())
    keys = [r["identity_hash"] for r in records]
    if [r["key"] for r in scores] != keys or len(set(keys)) != 6205:
        raise ValueError("sealed readout order or enrollment differs")
    available = set(keys)
    refs = {}
    with args.metadata.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            fold = int(row["strat_fold"])
            if fold == 10:
                continue
            key = identity(row["filename_lr"])
            if key not in available:
                continue
            codes, marker = ast.literal_eval(row["scp_codes"]), row["pacemaker"].strip().casefold()
            refs[key] = (fold, row["patient_id"], {e: disposition(e, codes, marker) for e in ENDPOINTS})
    if refs.keys() != available or any(refs[r["identity_hash"]][0] != r["fold"] for r in records):
        raise ValueError("cached reference membership differs")
    cal, held = ({patient for f, patient, _ in refs.values() if p(f)}
                 for p in (lambda f: f <= 8, lambda f: f == 9))
    if cal & held:
        raise ValueError("calibration and held patients overlap")
    audit = json.loads(args.support.read_bytes())
    reports = {}
    for label in ENDPOINTS:
        rows = [(refs[r["key"]][0], refs[r["key"]][1], refs[r["key"]][2][label], r["scores"][label])
                for r in scores]
        if Counter(x[2] for x in rows) != audit["endpoint_support"][label]["P4_scoreable"]["ECGs"]:
            raise ValueError("endpoint reference flow differs from independent support audit")

        c, cy, cp, _ = sample(rows, lambda f: f <= 8)
        h, y, p, g = sample(rows, lambda f: f == 9)
        u, uy, up, ug = sample(rows, lambda _: True)
        threshold = cutoff(cy, cp) if sufficient(c) and sufficient(h) else None
        if threshold is not None:
            calls = p >= threshold
            h["metrics"] = binary_metrics(y, calls.astype(int), p)
            h["metrics"]["npv"] = (h["metrics"]["tn"] / (h["metrics"]["tn"] + h["metrics"]["fn"])
                                   if h["metrics"]["tn"] + h["metrics"]["fn"] else None)
            h["cluster_intervals"] = bootstrap_binary_metrics(y, calls.astype(int), p, g, **DESIGN)
        if sufficient(u):
            m = binary_metrics(uy, np.zeros_like(uy), up)
            b = bootstrap_binary_metrics(uy, np.zeros_like(uy), up, ug, **DESIGN)
            u["rank_metrics"] = {k: m[k] for k in ("auroc", "average_precision")}
            u["cluster_intervals"] = {k: b["intervals"][k] for k in u["rank_metrics"]}
        reports[label] = {"calibration_folds_1_8": c, "held_fold_9": h, "pooled_descriptive_rank": u,
                          "new_operating_point": threshold, "released_operating_point_exists": False}
    write_new(args.output / "aggregate.json", {
        "schema": "TITAN_V45_PTBXL_CACHED_V3AG_RHYTHM_V1", "job": check["job"],
        "score_receipt_sha256": args.score_receipt_sha256, "reference_support_sha256": SUPPORT_SHA,
        "all_metadata_ecgs": 19601, "cached_scored_ecgs": 6205,
        "outside_authorized_scoreable_cache": 13396, "fold10_references_or_waveforms_used": False,
        "historical_independence_certified": False, "no_individual_records_exported": True,
        "calibration_and_held_subject_overlap": 0, "exact_signal_groups_crossing_folds": 0,
        "weights_changed": False, "endpoints": reports, "statistical_design": DESIGN,
    })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("score", "evaluate"))
    for key in ("repo", "assets", "features", "metadata", "support", "output"):
        parser.add_argument(f"--{key}", type=Path, required=True)
    parser.add_argument("--score-receipt-sha256")
    args = parser.parse_args()
    meta = args.features / "private_feature_metadata.json"
    if digest(meta) != FEATURE_META_SHA or digest(args.support) != SUPPORT_SHA:
        raise ValueError("unrecognized feature cache or reference support audit")
    index = json.loads(meta.read_bytes())["pathology_records"]
    records = [r for r in index if r["scored"]]
    if (len(index) != len(records) or len(records) != 6205
            or any(r["source"] != "ptbxl" or not 1 <= r["fold"] <= 9 for r in records)):
        raise ValueError("unexpected cached ECG cohort")
    if args.stage == "score":
        path = args.features / "private_frozen_features.npz"
        if digest(path) != CACHE_SHA:
            raise ValueError("private cache bytes differ")
        with np.load(path, allow_pickle=False) as archive:
            matrix = archive["p4_features"]
            if (matrix.shape != (6205, 670) or matrix.dtype != np.float32 or not np.isfinite(matrix).all()
                    or not np.array_equal(archive["p4_record_index"], np.arange(len(index)))):
                raise ValueError("unexpected private cache row alignment or representation")
        score(args, records, matrix)
    else:
        if digest(args.metadata) != SOURCE_SHA["metadata"]:
            raise ValueError("reference metadata differs from the audited source")
        evaluate(args, records)


if __name__ == "__main__":
    main()
