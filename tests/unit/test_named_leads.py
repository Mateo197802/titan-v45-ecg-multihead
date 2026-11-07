import numpy as np

from titan_v45.data.preprocessing import extract_named_leads


def test_uppercase_augmented_leads_are_not_replaced_with_zero_channels():
    signal = np.arange(24, dtype=np.float32).reshape(2, 12)
    names = ["I", "II", "III", "AVR", "AVL", "AVF", "V1", "V2", "V3", "V4", "V5", "V6"]
    values, mask = extract_named_leads(signal, names)
    np.testing.assert_array_equal(values, signal.T)
    assert mask.tolist() == [True] * 12


def test_uppercase_and_mixed_case_headers_map_to_identical_signals():
    signal = np.arange(6, dtype=np.float64).reshape(2, 3)
    a, a_mask = extract_named_leads(signal, ["AVR", "AVL", "AVF"])
    b, b_mask = extract_named_leads(signal, ["aVR", "aVL", "aVF"])
    np.testing.assert_array_equal(a, b)
    np.testing.assert_array_equal(a_mask, b_mask)
    assert a_mask.sum() == 3


def test_missing_leads_remain_missing_without_duplicating_a_channel():
    values, mask = extract_named_leads(np.array([[1.0, 2.0]]), ["II", "RESP"])
    assert mask.sum() == 1
    assert values[1, 0] == 1.0
    assert np.count_nonzero(values) == 1


def test_legacy_alias_and_first_occurrence_match_the_historical_contract():
    values, mask = extract_named_leads(np.array([[1.0, 2.0, 3.0]]), ["MLII", "II", "ECG2"])
    assert values[1, 0] == 2.0
    assert mask.sum() == 1


def test_empty_signal_preserves_the_requested_number_of_channels():
    values, mask = extract_named_leads(None, None)
    assert values.shape == (12, 0)
    assert not mask.any()
