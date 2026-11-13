"""Label-blind scoring helpers for the frozen SPH transfer evaluation."""
from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np

from titan_v45.models.frozen_pathology import P4_CLASSES
from titan_v45.models.frozen_rhythm import P6_CLASSES, P8_CLASSES, aggregate_rhythm


def score_sph_record(
    rhythm_windows: Sequence[tuple[np.ndarray, np.ndarray, np.ndarray]],
    pathology_window: tuple[np.ndarray, np.ndarray, np.ndarray],
    rhythm_scorer,
    pathology_scorer,
    rhythm_thresholds: Mapping[str, Mapping[str, float]],
):
    """Score one ECG without passing source diagnoses or patient metadata."""
    if not rhythm_windows:
        raise ValueError("at least one rhythm window is required")
    rhythm_logits, rhythm_aux = rhythm_scorer(rhythm_windows)
    pathology_primary, pathology_aux = pathology_scorer([pathology_window])[0]
    return summarize_sph_record(
        rhythm_logits, rhythm_aux, pathology_primary, pathology_aux, rhythm_thresholds,
        len(rhythm_windows), pathology_scorer.thresholds,
    )


def summarize_sph_record(
    rhythm_logits,
    rhythm_aux,
    pathology_primary,
    pathology_aux,
    rhythm_thresholds,
    rhythm_window_count,
    pathology_thresholds,
):
    profiles = {}
    for profile, classes in (("P6", P6_CLASSES), ("P8", P8_CLASSES)):
        threshold = dict(rhythm_thresholds[profile])
        if tuple(threshold) != classes:
            raise ValueError(f"unexpected {profile} threshold class order")
        decision = aggregate_rhythm(rhythm_logits[profile], threshold, profile=profile)
        profiles[profile] = {
            "scores": decision["scores"],
            "labels": list(decision["labels"]),
            "top1": decision["top1"],
            "used_fallback": bool(decision["used_fallback"]),
            "threshold_crossings": [
                label for label, score in decision["scores"].items()
                if score >= threshold[label]
            ],
            "auxiliary_scores": {
                f"backbone_{index}": float(np.asarray(rhythm_aux)[:, index].mean())
                for index in range(np.asarray(rhythm_aux).shape[1])
            },
        }
    if tuple(pathology_primary) != P4_CLASSES:
        raise ValueError("unexpected Primary4 class contract")
    if tuple(pathology_thresholds) != P4_CLASSES:
        raise ValueError("unexpected Primary4 threshold contract")
    p4_labels = [
        name for name, value in pathology_primary.items()
        if value >= pathology_thresholds[name]
    ]
    profiles["P4"] = {
        "scores": {name: float(value) for name, value in pathology_primary.items()},
        "labels": p4_labels,
        "top1": max(pathology_primary, key=pathology_primary.__getitem__),
        "used_fallback": False,
        "threshold_crossings": p4_labels,
        "auxiliary_scores": {name: float(value) for name, value in pathology_aux.items()},
    }
    return {"profiles": profiles, "rhythm_windows": rhythm_window_count}
