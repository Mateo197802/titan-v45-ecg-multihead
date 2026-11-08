"""Adapt native SPH arrays to the existing reconstructed preprocessing."""
from __future__ import annotations

from types import SimpleNamespace

import numpy as np

from titan_v45.data.reconstructed import prepare_p4_record, prepare_rhythm_record
from titan_v45.data.sph import FS_HZ, LEADS


class _ArrayReader:
    """Supply signal slices without consulting SPH clinical metadata."""

    def __init__(self, values):
        self.values = values

    def rdheader(self, _):
        return SimpleNamespace(fs=FS_HZ, sig_len=self.values.shape[1])

    def rdrecord(self, _, *, sampfrom, sampto):
        return SimpleNamespace(p_signal=self.values[:, sampfrom:sampto].T, sig_name=LEADS)


def prepare_sph_waveform(signal, morphology, *, branch):
    """Return label-free (12, 1250) windows on the native relative amplitude scale."""
    values = np.asarray(signal)
    if values.ndim != 2 or values.shape[0] != len(LEADS) or values.dtype.kind not in "fi":
        raise ValueError("invalid SPH waveform shape or dtype")
    if not 10 * FS_HZ <= values.shape[1] <= 60 * FS_HZ:
        raise ValueError("SPH duration is outside 10 to 60 seconds")
    if not np.isfinite(values).all():
        raise ValueError("nonfinite SPH waveform")
    values = values.astype(np.float64, copy=False)
    if not np.any(np.ptp(values, axis=1) > 0):
        raise ValueError("all SPH leads are flat")
    reader = _ArrayReader(values)
    if branch == "P4":
        windows = [prepare_p4_record("SPH", morphology, wfdb_module=reader)]
    elif branch == "rhythm":
        windows = prepare_rhythm_record("SPH", morphology, wfdb_module=reader)
    else:
        raise ValueError("unknown SPH specialist branch")
    if any(signal.shape != (12, 1250) or mask.shape != (12,) or features.shape != (10,)
           or not np.isfinite(signal).all() or not np.isfinite(features).all()
           for signal, mask, features in windows):
        raise ValueError("SPH prepared waveform contract failed")
    return windows
