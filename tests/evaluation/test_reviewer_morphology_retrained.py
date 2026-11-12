import runpy
import sys
from pathlib import Path

import numpy as np
import pytest

scripts = Path(__file__).resolve().parents[2] / "scripts/evaluation"
sys.path.insert(0, str(scripts))
try:
    m = runpy.run_path(str(scripts / "reviewer_morphology_retrained.py"))
finally:
    sys.path.remove(str(scripts))


def test_no_fold10_and_no_patient_or_exact_signal_cross_split():
    with pytest.raises(ValueError, match="fold 10"):
        m["assign"]({"fold": 10}, "P4", {})
    rows = [{"group_hash": "a", "identity_hash": "1"}, {"group_hash": "b", "identity_hash": "2"}]
    assert m["audit_split"](rows, ["train", "held"], {"1": "x", "2": "y"}) == {"train": 1, "held": 1}
    with pytest.raises(ValueError, match="overlap"):
        m["audit_split"](rows, ["train", "held"], {"1": "x", "2": "x"})


def test_optimizer_and_tie_safe_calibration():
    x = np.array([[-2.], [-1.], [1.], [2.]])
    y = np.array([0, 0, 1, 1])
    model = m["fit_head"](x, y, np.ones(4), .01, 200)
    assert model is not None
    scores = m["record_scores"](model, x, np.arange(4), np.arange(4), "P8")
    assert np.all(np.diff(scores) > 0)
    assert (scores >= m["threshold"](y, scores)).astype(int).tolist() == y.tolist()


def test_paired_bootstrap_uses_only_evaluable_held_groups():
    rows = [(np.array([1, 2]), np.array([0, 1]), np.array([0, 1]), np.array([0, 0]))]
    design = {"seed": 1, "replicates": 100, "level": .95}
    assert m["paired_macro"](rows, ["unused", "a", "b"], design) == m["paired_macro"](
        rows, ["another-train-patient", "a", "b", "calibration-only"], design,
    )
    assert m["paired_macro"](rows, ["unused", "a", "b"], design)["with_minus_without"] == 1
