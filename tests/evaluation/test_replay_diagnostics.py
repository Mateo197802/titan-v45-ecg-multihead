import pytest

from titan_v45.evaluation.replay_diagnostics import (
    binary_residuals,
    compare_pathology_replay_ledgers,
    ranking_residuals,
)


def test_binary_residual_separates_numerical_failure_from_unchanged_calls():
    report = binary_residuals([0.3, 0.501], [0.3002, 0.5009], 0.5)
    assert report["decision_changes"] == 0
    assert report["score"]["above_historical_atol"] == 2
    assert report["archived_margin_at_most_observed_max_error"] == 0
    assert report["minimum_replayed_margin"] == pytest.approx(0.0009)
    with pytest.raises(ValueError, match="probabilities"):
        binary_residuals([float("nan")], [0.1], 0.5)


def test_rank_inversion_respects_class_scores_and_never_emits_row_keys():
    report = ranking_residuals([[0.55, 0.54, 0.1]], [[0.53, 0.56, 0.1]], [0], [1])
    assert report["top1_changes"] == 1
    assert report["changes_with_same_top_two_candidates"] == 1
    assert report["changed_rows"]["archived_winner_margin_min"] == pytest.approx(0.01)
    assert report["changed_rows"]["new_winner_margin_min"] == pytest.approx(0.03)
    assert report["changed_rows"]["old_winner_minus_new_winner_after_replay_max"] < 0
    assert report["archived_margin_at_most_twice_observed_max_error"] == 1
    with pytest.raises(ValueError, match="argmax"):
        ranking_residuals([[0.55, 0.54]], [[0.53, 0.56]], [1], [1])


def test_p4_batch_comparison_requires_equal_coverage_and_separates_drift():
    left = {"one": {"primary_scores": {"ASMI": 0.1}}}
    right = {"one": {"primary_scores": {"ASMI": 0.2}}}
    result = compare_pathology_replay_ledgers(left, right, {"ASMI": 0.15})
    assert result["ASMI"]["decision_changes"] == 1
    assert result["ASMI"]["score"]["pairs"] == 1
    with pytest.raises(ValueError, match="coverage"):
        compare_pathology_replay_ledgers(left, {}, {"ASMI": 0.15})
