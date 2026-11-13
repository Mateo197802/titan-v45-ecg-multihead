import importlib
from pathlib import Path

import numpy as np
import pytest


@pytest.fixture
def runner(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts/evaluation"))
    return importlib.import_module("evaluate_reviewer_ptbxl_cached_rhythm")


def test_cutoff_groups_equal_scores_and_uses_highest_tie(runner):
    assert runner.cutoff(np.array([1, 0, 1, 0]), np.array([0.9, 0.8, 0.8, 0.1])) == 0.9
    assert runner.cutoff(np.array([0, 1]), np.array([0.5, 0.5])) > 0.5
    with pytest.raises(ValueError, match="polarities"):
        runner.cutoff(np.ones(2), np.array([0.9, 0.1]))


def test_minimum_is_unique_subjects_per_polarity(runner):
    assert not runner.sufficient({"positive_subjects": 4, "control_subjects": 900})
    assert runner.sufficient({"positive_subjects": 5, "control_subjects": 5})
