from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import gcd

import numpy as np
from scipy.signal import resample_poly


@dataclass(frozen=True)
class PreparedEcg:
    signal: np.ndarray
    lead_mask: np.ndarray
    target_fs: int


def prepare_ecg(
    signal: np.ndarray,
    *,
    source_fs: int,
    lead_indices: Sequence[int] | None = None,
    target_fs: int = 125,
    duration_seconds: int = 10,
) -> PreparedEcg:
    values = np.asarray(signal, dtype=np.float32)
    if values.ndim != 2:
        raise ValueError("signal must have shape [leads, time]")
    if source_fs <= 0 or target_fs <= 0:
        raise ValueError("sampling frequencies must be positive")
    indices = tuple(range(values.shape[0])) if lead_indices is None else tuple(int(x) for x in lead_indices)
    if len(indices) != values.shape[0]:
        raise ValueError("lead_indices must contain one index for each input lead")
    if len(indices) != len(set(indices)):
        raise ValueError("lead_indices contains duplicate entries")
    if any(index < 0 or index >= 12 for index in indices):
        raise ValueError("lead indices must be in the canonical range 0..11")

    divisor = gcd(int(source_fs), int(target_fs))
    resampled = resample_poly(values, target_fs // divisor, source_fs // divisor, axis=1)
    expected_length = int(target_fs * duration_seconds)
    canonical = np.zeros((12, expected_length), dtype=np.float32)
    lead_mask = np.zeros(12, dtype=bool)
    usable = min(expected_length, resampled.shape[1])
    for source_index, canonical_index in enumerate(indices):
        canonical[canonical_index, :usable] = resampled[source_index, :usable]
        lead_mask[canonical_index] = True
    return PreparedEcg(signal=canonical, lead_mask=lead_mask, target_fs=int(target_fs))
