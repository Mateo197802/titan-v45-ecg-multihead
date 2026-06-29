from __future__ import annotations

from titan_v45.training.optuna_objective import composite_primary_score


def test_optuna_objective_uses_frozen_primary_weights() -> None:
    assert composite_primary_score(primary8_macro_f1=0.60, primary4_macro_f1=0.80) == 0.68


def test_optuna_objective_penalizes_missing_primary_classes() -> None:
    score = composite_primary_score(
        primary8_macro_f1=0.60,
        primary4_macro_f1=0.80,
        missing_primary8=2,
        missing_primary4=1,
    )
    assert score == 0.53
