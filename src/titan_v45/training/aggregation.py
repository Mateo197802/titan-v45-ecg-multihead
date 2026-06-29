from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

import numpy as np


@dataclass(frozen=True)
class RecordProbabilities:
    record_ids: tuple[str, ...]
    probabilities: np.ndarray


def aggregate_record_probabilities(
    record_ids: Sequence[str],
    probabilities: np.ndarray,
    *,
    reduction: Literal["mean", "max"] = "mean",
) -> RecordProbabilities:
    scores = np.asarray(probabilities, dtype=np.float64)
    if scores.ndim != 2 or len(record_ids) != scores.shape[0]:
        raise ValueError("record ids must align with a two-dimensional probability array")
    if reduction not in {"mean", "max"}:
        raise ValueError("reduction must be 'mean' or 'max'")
    ordered = tuple(dict.fromkeys(str(record_id) for record_id in record_ids))
    rows: list[np.ndarray] = []
    normalized_ids = np.asarray([str(record_id) for record_id in record_ids], dtype=object)
    for record_id in ordered:
        selected = scores[normalized_ids == record_id]
        rows.append(selected.mean(axis=0) if reduction == "mean" else selected.max(axis=0))
    matrix = np.vstack(rows) if rows else np.empty((0, scores.shape[1]), dtype=np.float64)
    return RecordProbabilities(ordered, matrix)


def clean_top1_predictions(probabilities: np.ndarray) -> np.ndarray:
    scores = np.asarray(probabilities, dtype=np.float64)
    if scores.ndim != 2 or scores.shape[1] == 0:
        raise ValueError("probabilities must be a non-empty two-dimensional array")
    if not np.isfinite(scores).all():
        raise ValueError("probabilities must be finite")
    return np.argmax(scores, axis=1).astype(np.int64)
