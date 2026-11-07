"""Signal preparation for the declared P4 replay, not an original loader."""
from __future__ import annotations

from math import gcd

import numpy as np
from scipy.signal import butter, lfilter, resample_poly

from titan_v45.data.preprocessing import extract_named_leads


def prepare_p4_record(record_base, morphology, *, wfdb_module=None):
    """Apply the source-backed replay's fixed first-window WFDB contract."""
    if wfdb_module is None:
        import wfdb as wfdb_module

    header = wfdb_module.rdheader(str(record_base))
    fs = int(header.fs)
    if fs <= 1 or fs != header.fs or header.sig_len <= 0:
        raise ValueError("unsupported WFDB sample rate or length")
    record = wfdb_module.rdrecord(str(record_base), sampfrom=0, sampto=min(header.sig_len, 12 * fs))
    signal = np.pad(record.p_signal, ((2 * fs, max(0, 12 * fs - header.sig_len)), (0, 0)))
    values, mask = extract_named_leads(signal, record.sig_name)
    if not mask.any():
        raise ValueError("no recognized ECG leads")
    values = np.nan_to_num(values, nan=0.0, posinf=0.0, neginf=0.0)
    for i in range(12):
        if np.std(values[i]) > 1e-6:
            b, a = butter(3, [0.5 / (fs / 2), min(45 / (fs / 2), 0.99)], btype="band")
            values[i] = lfilter(b, a, values[i])
    divisor = gcd(fs, 125)
    values = resample_poly(values, 125 // divisor, fs // divisor, axis=1)[:, 250:1500]
    if values.shape != (12, 1250):
        raise ValueError("unexpected resampled shape")
    sd = values.std(axis=1, keepdims=True)
    sd[sd < 1e-6] = 1
    values = (values - values.mean(axis=1, keepdims=True)) / sd
    return values, mask, morphology(values, fs=125)


def historical_window_starts(samples: int, fs: int) -> tuple[int, ...]:
    """Recorded 10 s / 5 s stride schedule, including the final-window rule."""
    if fs <= 1 or samples <= 0:
        raise ValueError("invalid source duration or rate")
    size = int(samples * 125 / fs)
    if size <= 1250:
        return (0,)
    starts = list(range(0, size - 1250 + 1, 625))
    if size - (starts[-1] + 625) > 625:
        starts.append(size - 1250)
    return tuple(starts)


def prepare_rhythm_record(record_base, morphology, *, wfdb_module=None):
    """Recover candidate sliding windows without using a label or score."""
    if wfdb_module is None:
        import wfdb as wfdb_module

    header = wfdb_module.rdheader(str(record_base))
    fs = int(header.fs)
    if fs != header.fs:
        raise ValueError("non-integer source rate")
    starts = historical_window_starts(header.sig_len, fs)
    samples = []
    for start in starts:
        at = int(start * (fs / 125))
        first, last = at - 2 * fs, at + 12 * fs
        low, high = max(0, first), min(header.sig_len, last)
        record = wfdb_module.rdrecord(str(record_base), sampfrom=low, sampto=high)
        signal = np.pad(record.p_signal, ((low - first, last - high), (0, 0)))
        values, mask = extract_named_leads(signal, record.sig_name)
        if not mask.any():
            raise ValueError("no recognized ECG leads")
        values = np.nan_to_num(values, nan=0.0, posinf=0.0, neginf=0.0)
        for i in range(12):
            if np.std(values[i]) > 1e-6:
                b, a = butter(3, [0.5 / (fs / 2), min(45 / (fs / 2), 0.99)], btype="band")
                values[i] = lfilter(b, a, values[i])
        if fs != 125:
            divisor = gcd(fs, 125)
            values = np.stack([resample_poly(lead, 125 // divisor, fs // divisor)
                               for lead in values], axis=0).astype(np.float32)
        values = values[:, 250:1500]
        if values.shape != (12, 1250):
            raise ValueError("unexpected resampled shape")
        sd = values.std(axis=1, keepdims=True)
        sd[sd < 1e-6] = 1
        values = (values - values.mean(axis=1, keepdims=True)) / sd
        samples.append((values, mask, morphology(values, fs=125)))
    return samples
