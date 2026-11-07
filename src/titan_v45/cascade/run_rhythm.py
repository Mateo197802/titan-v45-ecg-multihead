"""Reconstructed rhythm waveform audit on the retained release inventory."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import torch

from titan_v45.cascade.policy import CASCADE_RHYTHMS
from titan_v45.cascade.run_pathology import (
    MORPHOLOGY_SHA,
    _extract_records,
    _load_morphology,
    _read_rows,
)
from titan_v45.cascade.waveform import build_waveform_inventory
from titan_v45.data.reconstructed import prepare_rhythm_record
from titan_v45.models.frozen_pathology import verified_assets
from titan_v45.models.frozen_rhythm import (
    BACKBONE,
    DATASET,
    HEADS,
    P6_CLASSES,
    P8_CLASSES,
    TRAINER_SHA,
    FrozenRhythm,
    aggregate_rhythm,
    load_recorded_event_extractor,
)

PACKAGE = "external-dev-rhythm-chapman-shaoxing"
BATCH_SIZE = 32


def _summarize(ledger, profile, archived):
    values = [v for v in ledger.values() if profile in v]
    result = {"inputs": len(archived), "scored_records": len(values),
              "windows": sum(v["windows"] for v in values),
              "top1_counts": dict(sorted(Counter(v[profile]["top1"] for v in values).items())),
              "fallback_count": sum(v[profile]["used_fallback"] for v in values),
              "window_count_disagreements": 0, "top1_disagreements": 0,
              "binary_set_disagreements": 0, "archived_comparison_pairs": 0,
              "max_absolute_score_difference": None, "quarantine_assessed": 0,
              "quarantine_rate": None}
    for row in archived:
        key = row["source"].casefold(), row["record_id"]
        current = ledger.get(key, {})
        if profile not in current:
            continue
        item = current[profile]
        result["archived_comparison_pairs"] += 1
        result["window_count_disagreements"] += current["windows"] != int(row["window_count"])
        top, score_prefix = ("pred_label", "prob_") if profile == "P6" else (
            "predicted_label", "membership_prob_"
        )
        result["top1_disagreements"] += item["top1"] != row[top]
        flags = ({c for c in P6_CLASSES if row["threshold_pass_" + c] in ("1", "True")}
                 if profile == "P6" else set(filter(None, row["predicted_labels"].split("|"))))
        result["binary_set_disagreements"] += set(item["labels"]) != flags
        error = max(abs(p - float(row[score_prefix + c])) for c, p in item["scores"].items())
        result["max_absolute_score_difference"] = max(
            result["max_absolute_score_difference"] or 0.0, error
        )
    return result


def run_rhythm_release(repo: Path, release: Path, scratch: Path, device: str):
    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but unavailable")
    assets, digests = verified_assets(repo, release, {BACKBONE, DATASET, *HEADS.values()})
    contract = json.loads((repo / "outputs/models/heads/global_head_contracts.json").read_text(encoding="utf-8"))
    archive = repo / "docs/provenance/recovered-original-sources-20261029.zip"
    scorer = FrozenRhythm(assets, contract, load_recorded_event_extractor(archive), device)
    morphology = _load_morphology(repo)
    p6_calibration = json.loads((repo / "outputs/results/revision_20261029/p6_calibration_lineage_summary.json")
                                .read_text(encoding="utf-8"))
    p8_metrics = json.loads((repo / "outputs/results/external_dev/rhythm_primary8_metrics.json")
                            .read_text(encoding="utf-8"))
    if (tuple(p6_calibration["classes"]) != P6_CLASSES or p6_calibration["biases"] != [0] * 6
            or p6_calibration["aggregation"] != "mean_logits" or tuple(p8_metrics["classes"]) != P8_CLASSES):
        raise ValueError("unexpected preserved score policy")
    thresholds = {"P6": dict(zip(P6_CLASSES, p6_calibration["thresholds"], strict=True)),
                  "P8": dict(zip(P8_CLASSES, p8_metrics["thresholds"], strict=True))}
    base = repo / "data/manifests/external_dev"
    p8_path, p6_path = base / "rhythm_primary8_records.csv", base / "rhythm_primary6_diagnostic_records.csv"
    p8, p6 = (build_waveform_inventory(_read_rows(path)) for path in (p8_path, p6_path))
    if any(p8.get(key) != path for key, path in p6.items()):
        raise ValueError("P6 is not a compatible subset of the P8 waveform inventory")
    ledger, errors = {}, Counter()
    with TemporaryDirectory(prefix="titan-rhythm-waveform-", dir=scratch) as work:
        work = Path(work)
        _extract_records(assets[DATASET], work, PACKAGE, (".hea", ".dat", ".mat"))
        items = list(p8.items())
        for start in range(0, len(items), BATCH_SIZE):
            samples, offsets = [], {}
            for key, path in items[start:start + BATCH_SIZE]:
                try:
                    prepared = prepare_rhythm_record(work / PACKAGE / path, morphology)
                except (OSError, ValueError) as exc:
                    errors[type(exc).__name__] += 1
                    ledger[key] = {"pre": "no_scores", "post": "no_scores", "error": type(exc).__name__}
                    continue
                offsets[key] = slice(len(samples), len(samples) + len(prepared))
                samples.extend(prepared)
            if not samples:
                continue
            chunks = [scorer(samples[n:n+BATCH_SIZE]) for n in range(0, len(samples), BATCH_SIZE)]
            logits = {profile: np.concatenate([part[0][profile] for part in chunks], axis=0)
                      for profile in HEADS}
            secondary = np.concatenate([part[1] for part in chunks], axis=0)
            for key, interval in offsets.items():
                row = {"windows": interval.stop - interval.start, "pre": "rhythm_only",
                       "post": "quarantine_not_assessed", "auxiliary_action": "no_frozen_policy",
                       "auxiliary_scores": dict(zip(CASCADE_RHYTHMS, secondary[interval]
                                                    .mean(axis=0, dtype=np.float64).tolist(), strict=True))}
                row["P8"] = aggregate_rhythm(logits["P8"][interval], thresholds["P8"], profile="P8")
                if key in p6:
                    row["P6"] = aggregate_rhythm(logits["P6"][interval], thresholds["P6"], profile="P6")
                ledger[key] = row
    evidence = repo / "outputs/results/external_dev/evidence"
    report = {
        "schema": "TITAN_V45_RECONSTRUCTED_RHYTHM_WAVEFORM_CASCADE_V1",
        "scope": "frozen_selected_rhythm_waveforms_new_inference_not_historical_cascade",
        "profiles": {profile: _summarize(ledger, profile, _read_rows(
            evidence / f"rhythm_primary{profile[-1]}_record_predictions.csv"
        )) for profile in HEADS},
        "input_error_counts": dict(sorted(errors.items())), "batch_size": BATCH_SIZE,
        "auxiliary_score_support": {c: sum("auxiliary_scores" in v for v in ledger.values())
                                    for c in CASCADE_RHYTHMS},
        "thresholds": thresholds, "weights_or_thresholds_modified": False,
        "checkpoint_hidden_widths": scorer.widths,
        "release_sha256": digests,
        "manifest_sha256_lf": {path.name: hashlib.sha256(path.read_bytes()
                                                         .replace(b"\r\n", b"\n")).hexdigest()
                               for path in (p6_path, p8_path)},
        "morphology_candidate_sha256_lf": MORPHOLOGY_SHA, "event_trainer_sha256": TRAINER_SHA,
        "auxiliary_action": "no_frozen_policy", "reference_labels_used_for_routing": False,
        "independent_external_evaluation": False, "historical_preprocessing_certified": False,
        "torch": torch.__version__, "device": device,
    }
    return report, ledger
