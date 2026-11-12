import numpy as np
import pytest

from titan_v45.data.duration_aware_preprocessing import (
    code_observed_window,
    masked_time_forward,
    normalize,
    observed_descriptors,
    prepare_observed,
)


def test_code_duration_is_not_invented_and_limb_geometry_is_linear():
    t = (np.arange(2934) + 1) / 400
    i, ii = np.sin(2 * np.pi * 1.4 * t), np.sin(2 * np.pi * 2.1 * t)
    waveform = np.column_stack([i, ii, ii - i, *([ii] * 9)])
    observed, duration = code_observed_window(np.pad(waveform, ((581, 581), (0, 0))))
    assert duration == "short_7p335"
    np.testing.assert_array_equal(observed, waveform)
    filtered = prepare_observed(observed, 400)
    assert filtered.shape == (12, 917)
    np.testing.assert_allclose(filtered[2], filtered[1] - filtered[0], atol=1e-6)
    assert observed_descriptors(filtered).shape == (7,)
    assert np.isfinite(normalize(filtered, "robust_shared_gain")).all()
    assert np.isfinite(normalize(filtered, "per_lead_zscore")).all()
    long = np.tile(np.arange(1, 4097)[:, None], (1, 12))
    assert code_observed_window(long)[0].shape == (4000, 12)
    with pytest.raises(ValueError, match="ambiguous_duration"):
        code_observed_window(np.pad(waveform, ((580, 582), (0, 0))))


def test_temporal_mask_drops_padding_before_model():
    torch = pytest.importorskip("torch")

    class Mean:
        @staticmethod
        def forward_features(x):
            return x.mean(dim=-1)

    wave = torch.tensor([[1., 2., 100.], [4., 5., 6.]])[:, None].expand(-1, 12, -1)
    mask = torch.tensor([[True, True, False], [True, True, True]])
    out = masked_time_forward(Mean(), wave, mask)
    assert out[:, 0].tolist() == [1.5, 5.]
    with pytest.raises(ValueError, match="contiguous"):
        masked_time_forward(Mean(), wave, torch.tensor([[True, False, True], [True, True, True]]))


def test_filter_preserves_synthetic_wave_timing_and_st_direction():
    fs = 400
    t = np.arange(4000) / fs
    lead = np.zeros_like(t)
    for beat in (2., 4., 6., 8.):
        for center, width, amplitude in ((-.17, .025, .12), (0, .016, 1.0), (.32, .055, .25)):
            lead += amplitude * np.exp(-.5 * ((t - beat - center) / width) ** 2)
        lead[(t >= beat + .07) & (t <= beat + .19)] += .14
    filtered = prepare_observed(np.column_stack([lead * (1 + i / 10) for i in range(12)]), fs)[0]
    for center in (3.83, 4., 4.32):
        k = round(center * 125)
        assert abs((k - 3 + np.argmax(filtered[k - 3:k + 4])) / 125 - center) <= .016
    assert filtered[round(4.12 * 125)] > filtered[round(3.60 * 125)] + .08
