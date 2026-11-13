"""Score waveform-QC eligible MIMIC records without reading diagnosis references."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import torch
from acquire_mimic import atomic
from audit_mimic_signals import read_physical

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/specialist_experiments"))
from extract_features import _atomic_npz, _pathology_batch, _rhythm_batch, _safe_morphology
from probe_frozen import load_scorers

from titan_v45.data.external_ecg import physical_digest, prepare_external
from titan_v45.models.frozen_pathology import P4_CLASSES
from titan_v45.models.frozen_rhythm import P6_CLASSES, P8_CLASSES

PROTOCOL = ROOT / "docs/external_validation_20261111/FROZEN_EXTERNAL_EVALUATION_PROTOCOL.json"


def run(study: Path, assets: Path):
    protocol = PROTOCOL.read_bytes()
    qc_path = study / "mimic_waveform_qc_receipt.json"
    qc_bytes = qc_path.read_bytes()
    qc = json.loads(qc_bytes)
    manifest = (study / "private_mimic_waveform_eligibility.jsonl").read_bytes()
    if hashlib.sha256(manifest).hexdigest() != qc["eligibility_manifest_sha256"]:
        raise ValueError("unsealed eligibility manifest")
    if qc["performance_computed"] is not False or qc["source_patient_split_overlap"] != 0:
        raise ValueError("invalid outcome-blind QC receipt")
    rows = [json.loads(line) for line in manifest.splitlines()]
    counts = Counter(row["analysis_status"] for row in rows)
    eligible = [(index, row) for index, row in enumerate(rows)
                if row["analysis_status"] == "waveform_eligible"]
    if not eligible:
        raise ValueError("empty eligible waveform cohort")
    output = study / "frozen_baseline_private"
    output.mkdir(exist_ok=False)
    rhythm, pathology, hashes, thresholds = load_scorers(assets, json.loads(protocol))
    morphology = _safe_morphology(ROOT)
    cache = {key: [] for key in ("P6", "P8", "P4")}
    scores = {key: [] for key in cache}
    scored_indices = []
    failures = []
    for start in range(0, len(eligible), 32):
        samples, indices = [], []
        for index, row in eligible[start:start + 32]:
            try:
                physical, _ = read_physical(study / "mimic" / row["path"])
                if physical_digest(physical, 500) != row["physical_digest"]:
                    raise ValueError("waveform_changed_since_qc")
                samples.append(prepare_external(physical, 500, morphology))
                indices.append(index)
            except (OSError, ValueError, RuntimeError) as error:
                failures.append({"manifest_row": index, "error": type(error).__name__})
        if not samples:
            continue
        rhythm_batch = _rhythm_batch(rhythm, samples)
        for key in ("P6", "P8"):
            features, logits = rhythm_batch[key]
            columns = [P8_CLASSES.index(c) for c in (P6_CLASSES if key == "P6" else P8_CLASSES)]
            projected = logits[:, columns]
            probabilities = (
                1 / (1 + np.exp(-np.clip(projected.astype(np.float64), -50, 50)))
                if key == "P6" else torch.as_tensor(projected).sigmoid().numpy()
            )
            scores[key].append(probabilities)
            cache[key].append(features)
        features, probabilities = _pathology_batch(pathology, samples)
        cache["P4"].append(features)
        scores["P4"].append(probabilities)
        scored_indices.extend(indices)
        if len(scored_indices) % 256 == 0:
            print(json.dumps({"scored": len(scored_indices), "errors": len(failures)}), flush=True)
    if not scored_indices:
        raise RuntimeError("no records scored")
    arrays = {f"{key}_features": np.concatenate(values) for key, values in cache.items()}
    probabilities = {key: np.concatenate(values) for key, values in scores.items()}
    arrays.update({f"{key}_scores": value for key, value in probabilities.items()})
    if any(len(value) != len(scored_indices) or not np.isfinite(value).all() for value in arrays.values()):
        raise RuntimeError("frozen output alignment or finiteness failure")
    classes = {"P6": P6_CLASSES, "P8": P8_CLASSES, "P4": P4_CLASSES}
    route = {}
    for key, class_names in classes.items():
        active = (probabilities[key] >= [thresholds[key][name] for name in class_names]).sum(axis=1)
        route[key] = {
            "threshold_set_empty": int((active == 0).sum()),
            "threshold_set_nonempty": int((active > 0).sum()),
            "top1_fallback_if_threshold_set_empty": int((active == 0).sum()) if key == "P8" else 0,
            "clinical_quarantine": "NOT_ASSESSED",
        }
    _atomic_npz(output / "features_and_scores.npz", manifest_row=np.asarray(scored_indices), **arrays)
    atomic(output / "private_score_failures.json", (json.dumps(failures) + "\n").encode())
    with (output / "features_and_scores.npz").open("rb") as stream:
        digest = hashlib.sha256()
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    receipt = {
        "scope": "FROZEN_MIMIC_INFERENCE_NO_REFERENCE_NO_PERFORMANCE",
        "protocol_sha256": hashlib.sha256(protocol).hexdigest(),
        "waveform_qc_receipt_sha256": hashlib.sha256(qc_bytes).hexdigest(),
        "private_cache_sha256": digest.hexdigest(),
        "baseline_asset_sha256": hashes,
        "classes": classes,
        "thresholds": thresholds,
        "manifest_rows": len(rows),
        "waveform_status_counts": counts,
        "eligible_ecgs": len(eligible),
        "scored_ecgs": len(scored_indices),
        "scored_patients": len({rows[idx]["subject_id"] for idx in scored_indices}),
        "failed_scoring": len(failures),
        "threshold_routing": route,
        "reference_read": False,
        "performance_computed": False,
    }
    encoded = (json.dumps(receipt, sort_keys=True, indent=2) + "\n").encode()
    atomic(output / "frozen_baseline_receipt.json", encoded)
    print(encoded.decode(), end="")


if __name__ == "__main__":
    import os

    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("study", type=Path)
    parser.add_argument("assets", type=Path)
    args = parser.parse_args()
    run(args.study, args.assets)
