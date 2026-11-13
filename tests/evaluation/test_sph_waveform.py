import numpy as np
import pytest

from titan_v45.data.sph_waveform import prepare_sph_waveform


def _morph(signal, *, fs):
    assert signal.shape == (12, 1250) and fs == 125
    return np.zeros(10, dtype=np.float32)


def test_fixed_waveform_processing_is_label_free_and_gain_invariant_on_fixture():
    t = np.arange(8000) / 500
    values = np.stack([np.sin(2 * np.pi * (i + 1) * t) for i in range(12)])
    for branch, expected in (("P4", 1), ("rhythm", 3)):
        samples = prepare_sph_waveform(values, _morph, branch=branch)
        assert len(samples) == expected
        for factor in (0.001, 10, 1000):
            scaled = prepare_sph_waveform(factor * values, _morph, branch=branch)
            assert len(scaled) == expected
            for (signal, mask, morph), (signal_scaled, _, _) in zip(samples, scaled, strict=True):
                assert signal.shape == (12, 1250)
                assert np.all(mask) and morph.shape == (10,)
                assert np.isfinite(signal).all()
                np.testing.assert_allclose(signal, signal_scaled, atol=1e-5, rtol=1e-5)


def test_invalid_waveforms_do_not_become_negative_predictions():
    with pytest.raises(ValueError, match="duration"):
        prepare_sph_waveform(np.ones((12, 4999)), _morph, branch="P4")
    with pytest.raises(ValueError, match="flat"):
        prepare_sph_waveform(np.ones((12, 5000)), _morph, branch="rhythm")
    bad = np.ones((12, 5000))
    bad[3, 1] = np.nan
    with pytest.raises(ValueError, match="nonfinite"):
        prepare_sph_waveform(bad, _morph, branch="P4")
