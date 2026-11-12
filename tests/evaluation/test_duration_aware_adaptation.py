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
