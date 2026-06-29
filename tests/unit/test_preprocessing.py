from __future__ import annotations

import numpy as np

from titan_v45.data.preprocessing import prepare_ecg


def test_prepare_ecg_resamples_to_canonical_shape_and_tracks_missing_leads() -> None:
    source = np.zeros((11, 5000), dtype=np.float32)
    prepared = prepare_ecg(source, source_fs=500, lead_indices=tuple(range(11)))

    assert prepared.signal.shape == (12, 1250)
    assert prepared.lead_mask.shape == (12,)
    assert prepared.lead_mask.tolist() == [True] * 11 + [False]
    assert prepared.target_fs == 125


def test_prepare_ecg_rejects_duplicate_lead_indices() -> None:
    source = np.zeros((2, 1000), dtype=np.float32)
    try:
        prepare_ecg(source, source_fs=100, lead_indices=(0, 0))
    except ValueError as error:
        assert "duplicate" in str(error)
    else:
        raise AssertionError("duplicate leads were accepted")
