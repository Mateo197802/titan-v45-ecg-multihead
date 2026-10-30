from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import gcd

import numpy as np
from scipy.signal import resample_poly

CANONICAL_12_LEADS = ("I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6")
LEAD_ALIASES = {
    "I": ("I", "ECG1"), "II": ("II", "MLII", "ML2", "ECG2", "ECG"),
    "III": ("III", "MLIII", "ML3"), "AVR": ("AVR",), "AVL": ("AVL",), "AVF": ("AVF",),
    **{f"V{i}": (f"V{i}", f"ECGV{i}") for i in range(1, 7)},
}
NON_ECG_TOKENS = ("RESP", "PLETH", "ABP", "BP", "PRESS", "PAP", "CVP", "ART")


def _lead_token(name: str) -> str:
    return "".join(ch for ch in str(name).upper() if ch.isalnum())


def _is_ecg_like_lead(name: str) -> bool:
    token = _lead_token(name)
    if not token or any(bad in token for bad in NON_ECG_TOKENS):
        return False
    if token in {"I", "II", "III", "AVR", "AVL", "AVF", "MLI", "MLII", "MLIII", "ECG"}:
        return True
    if token.startswith(("ECG", "ML")):
        return True
    return bool(token.startswith("V") and token[1:].isdigit())


def extract_named_leads(
    signals: np.ndarray | None, sig_names: Sequence[str] | None,
    target_leads: Sequence[str] = CANONICAL_12_LEADS,
) -> tuple[np.ndarray, np.ndarray]:
    """Recorded 19 June loader mapping: named channels, aliases, no synthesized leads.

    AVR/aVR spelling is equivalent. The first matching canonical name wins before
    aliases. Missing/non-ECG channels stay zero and have a false presence mask.
    """
    if signals is None or len(np.shape(signals)) != 2 or np.shape(signals)[1] == 0:
        return np.zeros((len(target_leads), 0), dtype=np.float32), np.zeros(len(target_leads), dtype=bool)
    token_to_index = {}
    for index, name in enumerate(sig_names or []):
        token = _lead_token(name)
        if token and token not in token_to_index:
            token_to_index[token] = index
    extracted, present = [], []
    for lead in target_leads:
        token = _lead_token(lead)
        selected = None
        for candidate in (token, *LEAD_ALIASES.get(token, ())):
            index = token_to_index.get(_lead_token(candidate))
            if index is not None and index < signals.shape[1] and _is_ecg_like_lead(sig_names[index]):
                selected = index
                break
        extracted.append(np.zeros(signals.shape[0], dtype=np.float32) if selected is None else signals[:, selected].astype(np.float32))
        present.append(selected is not None)
    return np.stack(extracted).astype(np.float32), np.asarray(present, dtype=bool)


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
