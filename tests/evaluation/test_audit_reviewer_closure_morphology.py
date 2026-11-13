import importlib
from pathlib import Path

import numpy as np
import pytest


@pytest.fixture
def audit(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts/evaluation"))
    return importlib.import_module("audit_reviewer_closure_morphology")


def test_paired_arm_swap_exact_point_and_null_when_arms_equal(audit):
    truth = np.array([1, 0, 1, 0])
    a, b = np.array([1, 0, 1, 0]), np.array([0, 1, 1, 0])
    groups = ["patient-a", "patient-a", "patient-b", "patient-c"]
    trials = [(np.arange(4), truth, a, b)]
    values = audit.arm_swap(audit.paired_counts(trials, groups), 100, 42)
    assert values["observed_delta_macro_f1"] == 0.5
    assert values["exchangeability_units"] == 3
    equal = [(np.arange(4), truth, a, a)]
    result = audit.arm_swap(audit.paired_counts(equal, groups), 100, 42)
    assert result["observed_delta_macro_f1"] == 0
    assert result["two_sided_monte_carlo_p"] == 1


def test_holm_controls_the_family_and_preserves_monotonicity(audit):
    assert audit.holm({"P6": 0.04, "P8": 0.015, "P4": 0.7}) == pytest.approx(
        {"P6": 0.08, "P8": 0.045, "P4": 0.7})
