"""Lightweight ECG morphology proxies for TITAN V4.

These features are intentionally cheap and deterministic. They are not
clinical-grade interval measurements; they are normalized auxiliary signals for
boundary decisions such as NSR/STACH, NSR/1AVB and NSR/RBBB.
"""
from __future__ import annotations

import math
from statistics import median

import numpy as np


MORPHOLOGY_FEATURE_NAMES = [
    "hr_median_bpm",
    "rrv_cv",
    "rrv_rmssd_ms",
    "qrs_width_proxy_ms",
    "p_to_r_proxy_ms",
    "qrs_band_ratio",
    "lowfreq_ratio",
    "hf_ratio",
    "lead_corr_abs_mean",
    "limb_qrs_asymmetry",
]
MORPHOLOGY_FEATURE_DIM = len(MORPHOLOGY_FEATURE_NAMES)


def _band_ratio(power: np.ndarray, freqs: np.ndarray, low: float, high: float) -> float:
    total = float(np.sum(power))
    if total <= 1e-12:
        return 0.0
    mask = (freqs >= float(low)) & (freqs <= float(high))
    return float(np.sum(power[mask]) / total)


def _select_peaks(values: np.ndarray, *, fs: int, min_distance_sec: float = 0.28) -> list[int]:
    values = np.asarray(values, dtype=np.float64)
    if values.size < 3:
        return []
    threshold = max(float(np.percentile(values, 88)), float(np.mean(values) + 0.8 * np.std(values)))
    candidates = np.where(
        (values[1:-1] >= values[:-2])
        & (values[1:-1] >= values[2:])
        & (values[1:-1] >= threshold)
    )[0] + 1
    ordered = sorted(candidates.astype(int).tolist(), key=lambda idx: float(values[idx]), reverse=True)
    min_distance = max(1, int(round(min_distance_sec * fs)))
    selected: list[int] = []
    for idx in ordered:
        if all(abs(idx - prev) >= min_distance for prev in selected):
            selected.append(int(idx))
    return sorted(selected)


def _best_rhythm_lead(signal: np.ndarray) -> np.ndarray:
    std = np.std(signal, axis=1)
    if signal.shape[0] > 1 and std[1] > 1e-6:
        return signal[1]
    return signal[int(np.argmax(std))]


def _estimate_qrs_width_ms(lead: np.ndarray, peaks: list[int], fs: int) -> float:
    widths: list[float] = []
    radius = max(4, int(round(0.18 * fs)))
    for peak in peaks:
        left = max(0, int(peak) - radius)
        right = min(lead.size, int(peak) + radius + 1)
        segment = np.abs(lead[left:right] - np.median(lead[left:right]))
        if segment.size < 3:
            continue
        amp = float(np.max(segment))
        if amp <= 1e-9:
            continue
        threshold = max(0.35 * amp, float(np.percentile(segment, 70)))
        active = np.where(segment >= threshold)[0]
        if active.size:
            widths.append(1000.0 * float(active[-1] - active[0] + 1) / float(fs))
    return float(median(widths)) if widths else math.nan


def _estimate_p_to_r_ms(lead: np.ndarray, peaks: list[int], fs: int) -> float:
    intervals: list[float] = []
    for peak in peaks:
        r = int(peak)
        start = max(0, r - int(round(0.28 * fs)))
        end = max(0, r - int(round(0.08 * fs)))
        if end <= start + 2:
            continue
        segment = np.abs(lead[start:end] - np.median(lead[start:end]))
        if segment.size < 3:
            continue
        p_idx = start + int(np.argmax(segment))
        interval_ms = 1000.0 * (r - p_idx) / float(fs)
        if 60.0 <= interval_ms <= 320.0:
            intervals.append(interval_ms)
    return float(median(intervals)) if intervals else math.nan


def _lead_corr_abs_mean(signal: np.ndarray) -> float:
    std = np.std(signal, axis=1)
    valid = [idx for idx, value in enumerate(std) if value > 1e-6]
    if len(valid) < 2:
        return math.nan
    corr = np.corrcoef(signal[valid])
    upper = corr[np.triu_indices_from(corr, k=1)]
    values = [abs(float(v)) for v in upper if math.isfinite(float(v))]
    return float(np.mean(values)) if values else math.nan


def compute_morphology_features(signal: np.ndarray, fs: int = 125) -> dict[str, float | int]:
    x = np.asarray(signal, dtype=np.float64)
    if x.ndim == 3:
        x = x[0]
    if x.ndim != 2:
        raise ValueError(f"signal must be [channels, samples], got {x.shape}")
    x = np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)

    lead = _best_rhythm_lead(x)
    detector = np.abs(lead - np.median(lead))
    peaks = _select_peaks(detector, fs=fs)
    rr = np.diff(peaks) / float(fs) if len(peaks) >= 2 else np.asarray([], dtype=np.float64)
    rr = rr[rr > 1e-6]

    hr = float(60.0 / np.median(rr)) if rr.size else math.nan
    rrv_cv = float(np.std(rr) / np.mean(rr)) if rr.size and float(np.mean(rr)) > 1e-9 else math.nan
    rmssd = float(np.sqrt(np.mean(np.diff(rr) ** 2)) * 1000.0) if rr.size >= 2 else math.nan

    freqs = np.fft.rfftfreq(x.shape[1], d=1.0 / float(fs))
    power = np.abs(np.fft.rfft(x, axis=1)) ** 2
    mean_power = np.mean(power, axis=0)
    qrs_mask = (freqs >= 5.0) & (freqs <= 18.0)
    limb_qrs_asymmetry = math.nan
    if x.shape[0] >= 6:
        lead_i_power = float(np.sum(power[0, qrs_mask]))
        avf_power = float(np.sum(power[5, qrs_mask]))
        limb_qrs_asymmetry = float((lead_i_power - avf_power) / max(lead_i_power + avf_power, 1e-12))

    return {
        "r_peak_count": int(len(peaks)),
        "hr_median_bpm": hr,
        "rrv_cv": rrv_cv,
        "rrv_rmssd_ms": rmssd,
        "qrs_width_proxy_ms": _estimate_qrs_width_ms(lead, peaks, fs),
        "p_to_r_proxy_ms": _estimate_p_to_r_ms(lead, peaks, fs),
        "qrs_band_ratio": _band_ratio(mean_power, freqs, 5.0, 18.0),
        "lowfreq_ratio": _band_ratio(mean_power, freqs, 0.0, 0.7),
        "hf_ratio": _band_ratio(mean_power, freqs, 35.0, fs / 2.0),
        "lead_corr_abs_mean": _lead_corr_abs_mean(x),
        "limb_qrs_asymmetry": limb_qrs_asymmetry,
    }


def _norm(value: float, scale: float, default: float = 0.0, low: float = 0.0, high: float = 1.0) -> float:
    if not math.isfinite(float(value)):
        return float(default)
    return float(np.clip(float(value) / float(scale), low, high))


def normalized_morphology_features(signal: np.ndarray, fs: int = 125) -> np.ndarray:
    raw = compute_morphology_features(signal, fs=fs)
    values = [
        _norm(raw["hr_median_bpm"], 220.0),
        _norm(raw["rrv_cv"], 1.0),
        _norm(raw["rrv_rmssd_ms"], 500.0),
        _norm(raw["qrs_width_proxy_ms"], 220.0),
        _norm(raw["p_to_r_proxy_ms"], 320.0),
        _norm(raw["qrs_band_ratio"], 1.0),
        _norm(raw["lowfreq_ratio"], 1.0),
        _norm(raw["hf_ratio"], 1.0),
        _norm(raw["lead_corr_abs_mean"], 1.0),
        _norm(raw["limb_qrs_asymmetry"], 1.0, default=0.0, low=-1.0, high=1.0),
    ]
    return np.asarray(values, dtype=np.float32)
