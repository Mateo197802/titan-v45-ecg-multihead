"""Preprocess observed samples only; preserve the historical CODE scorer separately."""
from __future__ import annotations

from functools import lru_cache
from math import gcd

import numpy as np
from scipy.signal import butter, resample_poly, sosfiltfilt, welch


def code_observed_window(samples):
    x = np.asarray(samples)
    if x.shape != (4096, 12) or not np.isfinite(x).all():
        raise ValueError("invalid_code_array")
    nonzero = np.flatnonzero(np.any(x != 0, axis=1))
    if not len(nonzero):
        raise ValueError("all_zero")
    borders = int(nonzero[0]), 4095 - int(nonzero[-1])
    if borders == (581, 581):
        return x[581:-581], "short_7p335"
    if borders in {(0, 0), (48, 48)}:
        return x[48:-48], "long_10"
    raise ValueError("ambiguous_duration")


@lru_cache(maxsize=8)
def _bandpass(fs):
    return butter(3, (0.05, 45.0), btype="bandpass", fs=fs, output="sos")


def prepare_observed(samples, fs, *, target=125):
    x = np.asarray(samples, dtype=np.float64)
    if (x.ndim != 2 or x.shape[1] != 12 or fs not in (400, 500)
            or not 7 * fs <= len(x) <= 10 * fs or not np.isfinite(x).all()):
        raise ValueError("invalid_observed_waveform")
    if np.any(np.ptp(x, axis=0) <= 1e-6):
        raise ValueError("flat_lead")
    ratio = gcd(fs, target)
    filtered = sosfiltfilt(_bandpass(fs), x, axis=0)
    result = resample_poly(filtered, target // ratio, fs // ratio, axis=0, padtype="line")
    if result.shape != ((len(x) * target + fs - 1) // fs, 12) or not np.isfinite(result).all():
        raise ValueError("invalid_resampled_waveform")
    return np.ascontiguousarray(result.T, dtype="<f4")


def normalize(x, mode):
    if mode == "per_lead_zscore":
        center = x.mean(axis=-1, keepdims=True)
        scale = x.std(axis=-1, keepdims=True)
    elif mode == "robust_shared_gain":
        center = np.median(x, axis=-1, keepdims=True)
        scale = 1.4826 * np.median(np.median(np.abs(x - center), axis=-1), axis=-1)[..., None, None]
    else:
        raise ValueError("unknown normalization")
    return np.asarray((x - center) / np.maximum(scale, 1e-6), dtype=np.float32)


def observed_descriptors(x, fs=125):
    """Small lead-II spectral/shape summary on the observed window only."""
    lead = np.asarray(x)[1]
    frequencies, power = welch(lead, fs=fs, nperseg=min(256, len(lead)))
    total = max(float(power.sum()), 1e-12)
    bands = [float(power[(frequencies >= low) & (frequencies < high)].sum() / total)
             for low, high in ((0.05, 1), (1, 5), (5, 15), (15, 45))]
    return np.asarray([*bands, np.std(lead), np.max(np.abs(lead)), np.std(np.diff(lead))], dtype=np.float32)


def masked_time_forward(backbone, waveforms, time_mask):
    """Bucket by valid prefix; zero padding never reaches convolution or attention."""
    import torch

    if waveforms.ndim != 3 or waveforms.shape[1] != 12 or time_mask.shape != waveforms.shape[::2]:
        raise ValueError("invalid temporal mask shape")
    if time_mask.dtype != torch.bool:
        raise ValueError("temporal mask must be boolean")
    lengths = time_mask.sum(dim=1)
    if torch.any(lengths == 0) or not torch.equal(
        time_mask, torch.arange(waveforms.shape[-1], device=waveforms.device)[None, :] < lengths[:, None]
    ):
        raise ValueError("mask must describe a nonempty contiguous observed prefix")
    outputs, indices = [], []
    for length in torch.unique(lengths).tolist():
        ids = torch.where(lengths == length)[0]
        indices.append(ids)
        outputs.append(backbone.forward_features(waveforms[ids, :, :length]))
    return torch.cat(outputs)[torch.argsort(torch.cat(indices))]
