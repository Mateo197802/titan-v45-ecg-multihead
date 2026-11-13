"""Physical-input checks for the external study; never pad short CODE recordings."""
from __future__ import annotations

import hashlib
from math import gcd

import numpy as np
from scipy.signal import butter, lfilter, resample_poly

from titan_v45.data.preprocessing import CANONICAL_12_LEADS

LEADS = tuple(lead.upper() for lead in CANONICAL_12_LEADS)
CODE_LEADS = ("I", "II", "III", "AVR", "AVL", "AVF", "V1", "V2", "V3", "V4", "V5", "V6")


def physical_mv(samples, names, units, fs: int):
    names = tuple(str(name).strip().upper() for name in names)
    if len(names) != 12 or set(names) != set(LEADS) or len(units) != 12:
        raise ValueError("invalid_canonical_leads")
    values = np.asarray(samples)
    if fs not in (400, 500) or values.shape != (10 * fs, 12):
        raise ValueError("invalid_rate_or_duration")
    scales = {"mv": 1.0, "uv": 0.001, "v": 1000.0}
    ordered = []
    for name in LEADS:
        index = names.index(name)
        unit = str(units[index]).strip().lower().replace("\u00b5", "u").replace("\u03bc", "u")
        if unit not in scales:
            raise ValueError("unknown_physical_unit")
        ordered.append(values[:, index].astype(np.float64) * scales[unit])
    signal = np.asarray(ordered, dtype=np.float32)
    if not np.isfinite(signal).all():
        raise ValueError("nonfinite_signal")
    if np.any(np.ptp(signal, axis=1) <= 1e-6):
        raise ValueError("flat_lead")
    return signal


def unpad_code(samples):
    values = np.asarray(samples)
    if values.shape != (4096, 12) or not np.isfinite(values).all():
        raise ValueError("invalid_code_array")
    if np.any(values[:48]) or np.any(values[-48:]):
        raise ValueError("unexpected_code_padding")
    if not np.any(values[:648]) and not np.any(values[-648:]):
        raise ValueError("short_or_ambiguous_code_duration")
    return values[48:-48]


def prepare_external(signal, fs, morphology):
    divisor = gcd(fs, 125)
    b, a = butter(3, [0.5 / (fs / 2), 45 / (fs / 2)], btype="band")
    padded = np.pad(signal, ((0, 0), (2 * fs, 2 * fs)))
    filtered = lfilter(b, a, padded, axis=1).astype(np.float32)
    values = resample_poly(filtered, 125 // divisor, fs // divisor, axis=1)[:, 250:1500]
    if values.shape != (12, 1250) or not np.isfinite(values).all():
        raise ValueError("invalid_preprocessed_signal")
    spread = values.std(axis=1, keepdims=True)
    spread[spread < 1e-6] = 1
    values = (values - values.mean(axis=1, keepdims=True)) / spread
    return values, np.ones(12, dtype=bool), morphology(values, fs=125)


def physical_digest(signal, fs):
    digest = hashlib.sha256()
    digest.update(int(fs).to_bytes(4, "little"))
    digest.update(np.ascontiguousarray(signal, dtype="<f4").tobytes())
    return digest.hexdigest()
