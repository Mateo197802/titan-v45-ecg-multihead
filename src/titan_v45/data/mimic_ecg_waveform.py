"""Strict WFDB input contract for MIMIC-IV-ECG v1.0 waveforms."""
from __future__ import annotations

import hashlib
from pathlib import Path, PurePosixPath

import numpy as np

from titan_v45.data.preprocessing import extract_named_leads
from titan_v45.data.sph_waveform import prepare_sph_waveform

_CANONICAL_LEADS = ("I", "II", "III", "AVR", "AVL", "AVF",
                    "V1", "V2", "V3", "V4", "V5", "V6")


def _lead_token(value):
    return "".join(character for character in str(value).upper() if character.isalnum())


def _zero_morphology(_signal, *, fs):
    if fs != 125:
        raise ValueError("unexpected morphology sampling rate")
    return np.zeros(10, dtype=np.float32)


def resolve_mimic_record_base(source_root, relative_path):
    """Resolve one record-list path without allowing traversal or symlinked files."""
    root = Path(source_root).resolve()
    relative = PurePosixPath(str(relative_path))
    if (relative.is_absolute() or ".." in relative.parts or "\\" in str(relative_path)
            or not relative.parts or relative.parts[0] != "files"):
        raise ValueError("unsafe MIMIC waveform path")
    base = root.joinpath(*relative.parts)
    if not base.resolve().is_relative_to(root):
        raise ValueError("unsafe MIMIC waveform path")
    for suffix in (".hea", ".dat"):
        member = Path(f"{base}{suffix}")
        if (member.is_symlink() or not member.is_file()
                or not member.resolve().is_relative_to(root)):
            raise ValueError("MIMIC waveform member is missing or unsafe")
    return base


def prepare_mimic_waveform(record_base, *, wfdb_module=None):
    """Read one 10-second ECG and apply the frozen 12-lead rhythm preprocessing."""
    if wfdb_module is None:
        import wfdb as wfdb_module

    header = wfdb_module.rdheader(str(record_base))
    if header.fs != 500 or header.sig_len != 5000 or header.n_sig != 12:
        raise ValueError("MIMIC waveform must satisfy the 10-second, 500 Hz, 12-lead contract")
    header_names = tuple(_lead_token(name) for name in header.sig_name)
    if (len(header_names) != 12 or len(set(header_names)) != 12
            or set(header_names) != set(_CANONICAL_LEADS)):
        raise ValueError("MIMIC waveform lacks the canonical 12-lead set")
    units = tuple(str(unit).strip().lower() for unit in header.units)
    if len(units) != 12 or any(unit != "mv" for unit in units):
        raise ValueError("MIMIC waveform must declare mV units on all 12 leads")

    record = wfdb_module.rdrecord(
        str(record_base), sampfrom=0, sampto=header.sig_len
    )
    record_names = tuple(_lead_token(name) for name in record.sig_name)
    values = np.asarray(record.p_signal)
    if (record_names != header_names or values.shape != (5000, 12)
            or values.dtype.kind not in "fi" or not np.isfinite(values).all()):
        raise ValueError("MIMIC WFDB samples do not match the validated header")
    canonical, lead_mask = extract_named_leads(values, record.sig_name)
    if not lead_mask.all() or not np.isfinite(canonical).all():
        raise ValueError("MIMIC waveform could not be mapped to every canonical lead")

    canonical_f64 = canonical.astype("<f8", copy=False)
    digest = hashlib.sha256(canonical_f64.tobytes()).hexdigest()
    windows = prepare_sph_waveform(canonical, _zero_morphology, branch="rhythm")
    return {
        "windows": windows,
        "signal_sha256": digest,
        "max_abs_mv": float(np.abs(canonical_f64).max()),
    }
