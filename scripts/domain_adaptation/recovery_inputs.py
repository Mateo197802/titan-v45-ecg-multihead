"""Development-only readers and waveform diagnostics for the recovery study."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import torch
from evaluate_released import load_released, score_released
from train_duration_aware import (
    ROOT,
    TemporalSpecialist,
    batches,
    digest,
    read_bank,
    read_extra,
    write_json,
)

from titan_v45.models.factory import build_titan_v45_backbone

RECOVERY = ROOT / "docs/performance_recovery/MODEL_PERFORMANCE_RECOVERY_PROTOCOL.json"
DEVELOPMENT = ("train", "validation", "calibration")
SOURCES = {"chapman": ("chapman_shaoxing", "validation"), "cpsc": ("cpsc2018", "train")}


def config():
    return json.loads(RECOVERY.read_bytes())


def authorized_bank(bank, split, normalizer):
    if split not in DEVELOPMENT:
        raise ValueError("only registered development splits may be opened")
    if digest(bank / "CODE_DEVELOPMENT_RECEIPT.json") != config()["code_bank_sha256"]:
        raise ValueError("unexpected CODE bank")
    return read_bank(bank, split, normalizer)


def authorized_extra(bank, source, split, normalizer):
    if (source, split) not in (("chapman_shaoxing", "train"), *SOURCES.values()):
        raise ValueError("unregistered source or split")
    if digest(bank / "ADDITIONAL_SOURCE_RECEIPT.json") != config()["other_bank_sha256"]:
        raise ValueError("unexpected transfer bank")
    return read_extra(bank, source, split, normalizer)


def audit_splits(bank):
    receipt = json.loads((bank / "CODE_DEVELOPMENT_RECEIPT.json").read_bytes())
    if digest(bank / "CODE_DEVELOPMENT_RECEIPT.json") != config()["code_bank_sha256"]:
        raise ValueError("unexpected CODE bank")
    groups, waves, exams, summary = {}, {}, {}, {}
    for split in DEVELOPMENT:
        path = bank / f"private_{split}.json"
        if digest(path) != receipt["splits"][split]["private_manifest_sha256"]:
            raise ValueError("partition manifest changed")
        rows = json.loads(path.read_bytes())
        if any(r["split"] != split for r in rows):
            raise ValueError("partition row does not belong to its split")
        groups[split] = {str(r["patient"]) for r in rows}
        waves[split] = {r["waveform_sha256"] for r in rows}
        exams[split] = {r["exam"] for r in rows}
        pr6 = {p for p in groups[split] if hashlib.sha256(f"20261112|pr6-code15|{p}".encode()).digest()[0] < 32}
        if pr6 != {str(r["patient"]) for r in rows if r["historical_pr6_patient"]} or (split != "train" and pr6):
            raise ValueError("PR6 patient selection predicate violates manifest contract")
        summary[split] = {"ecgs": len(rows), "patients": len(groups[split]), "pr6_eligible_patients": len(pr6),
                          "manifest_sha256": digest(path)}
    for i, first in enumerate(DEVELOPMENT):
        for second in DEVELOPMENT[i + 1:]:
            if any(collection[first] & collection[second] for collection in (groups, waves, exams)):
                raise ValueError("development partition overlap")
    return {"splits": summary, "cross_split_patient_exam_and_exact_waveform_overlap": 0,
            "pr6_eligibility_is_not_verified_pr6_test_membership": True, "historical_test_opened": False}


def parent_model(previous, seed):
    path = previous / f"partial_transformer_resnet_mlp-per_lead_zscore-{seed}" / "best.pt"
    if digest(path) != config()["parent_checkpoints"][str(seed)]:
        raise ValueError("parent checkpoint digest mismatch")
    saved = torch.load(path, map_location="cpu", weights_only=True)
    if saved["seed"] != seed or saved["normalizer"] != "per_lead_zscore":
        raise ValueError("parent checkpoint contract mismatch")
    model = TemporalSpecialist(build_titan_v45_backbone())
    model.load_state_dict(saved["state_dict"], strict=True)
    return model


def rr_features(wave):
    """Cross-lead QRS agreement gates HR/RR estimates; zero means missing."""
    from wfdb.processing import xqrs_detect

    try:
        ii, v2 = (xqrs_detect(wave[i].astype(float) * .25, fs=125, verbose=False) for i in (1, 7))
    except (ValueError, IndexError, ZeroDivisionError):
        return np.zeros(4, dtype=np.float32)
    if len(ii) < 4 or len(v2) < 4:
        return np.zeros(4, dtype=np.float32)
    distance = np.abs(ii[:, None] - v2)
    nearest = distance.argmin(axis=1)
    agreement = len(set(nearest[distance.min(axis=1) <= 10])) / max(len(ii), len(v2))
    rr = np.diff(ii) / 125.
    if agreement < .75 or np.any((rr < .25) | (rr > 2.5)):
        return np.asarray([0, 0, agreement, 0], dtype=np.float32)
    return np.asarray([60 / np.median(rr), rr.std() / rr.mean(), agreement, 1], dtype=np.float32)


def score_model(model, bank, *, rr=None):
    result = {key: [] for key in ("p", "labels", "exams", "patients", "durations", "noise_proxy", "rr")}
    model.eval()
    with torch.inference_mode():
        for wave, descriptors, y, _, exams, patients in batches(bank, config()["training"]["batch_size"]):
            x, d = torch.as_tensor(wave, device="cuda"), torch.as_tensor(descriptors, device="cuda")
            p = (model(x, d) if rr is None else model(x, d, torch.as_tensor(
                np.asarray([rr[str(e)] for e in exams]), device="cuda"))).sigmoid().cpu().numpy()
            for key, values in (("p", p), ("labels", y), ("exams", exams), ("patients", patients),
                                ("durations", np.full(len(y), wave.shape[-1])), ("noise_proxy", descriptors[:, 3])):
                result[key].append(values)
    return {key: np.concatenate(values) for key, values in result.items() if values}


def feature_map(bank):
    workers = min(12, max(1, int(os.getenv("SLURM_CPUS_PER_TASK", "1"))))
    out = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for values in bank.values():
            for start in range(0, len(values[0]), 256):
                stop = start + 256
                for key, feats in zip(values[4][start:stop], pool.map(rr_features, values[0][start:stop]), strict=True):
                    out[str(key)] = feats
    return out


def diagnose(previous, assets, out):
    code, extra = previous / "code-bank", previous / "additional-sources-v2"
    membership = audit_splits(code)
    incumbent = parent_model(previous, config()["incumbent_seed"]).cuda()
    for seed in config()["parent_checkpoints"]:
        # Hash all three physical files without allocating their tensor state.
        path = previous / f"partial_transformer_resnet_mlp-per_lead_zscore-{seed}" / "best.pt"
        if digest(path) != config()["parent_checkpoints"][seed]:
            raise ValueError("registered parent checkpoint changed")
    released, thresholds, hashes = load_released(assets)
    out.mkdir(mode=0o700, exist_ok=False)
    paths = {}
    for scope in ("validation", "calibration", "chapman", "cpsc"):
        normalizer = "per_lead_zscore"
        data = (authorized_extra(extra, *SOURCES[scope], normalizer) if scope in SOURCES
                else authorized_bank(code, scope, normalizer))
        old = score_model(incumbent, data)
        rr = feature_map(data)
        old["rr"] = np.asarray([rr[str(e)] for e in old["exams"]])
        if scope not in SOURCES:
            pub, y, exam, patient, durations = score_released(released, data, 32, config()["endpoints"])
            if any(not np.array_equal(left, old[key]) for key, left in
                   (("labels", y), ("exams", exam), ("patients", patient), ("durations", durations))):
                raise ValueError("released scores do not align with incumbent rows")
            old.update(pub)
        path = out / f"private_{scope}.npz"
        np.savez_compressed(path, **old)
        paths[path.name] = digest(path)
        print(json.dumps({"scope": scope, "scored_ecgs": len(old["labels"])}), flush=True)
        del data
    train = authorized_bank(code, "train", "per_lead_zscore")
    rr = feature_map(train)
    scores = score_model(incumbent, train)
    path = out / "private_training_aux.npz"
    np.savez_compressed(path, exams=scores["exams"], p=scores["p"], rr=np.asarray([rr[str(e)] for e in scores["exams"]]))
    paths[path.name] = digest(path)
    result = {"protocol_sha256": digest(RECOVERY), "split_audit": membership,
              "verified_parent_checkpoints": config()["parent_checkpoints"], "verified_released_assets": hashes,
              "published_thresholds": thresholds, "private_artifact_sha256": paths, "slurm_job": os.getenv("SLURM_JOB_ID"),
              "code_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()}
    write_json(out / "DEVELOPMENT_SCORING_RECEIPT.json", result)
    print(json.dumps(result, sort_keys=True), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("previous", "assets", "output"):
        parser.add_argument(key, type=Path)
    args = parser.parse_args()
    diagnose(args.previous, args.assets, args.output)
