import runpy
import sys
from pathlib import Path

import pytest

scripts = Path(__file__).resolve().parents[2] / "scripts/evaluation"
sys.path.insert(0, str(scripts))
try:
    module = runpy.run_path(str(scripts / "audit_reviewer_auxiliary_support.py"))
finally:
    sys.path.remove(str(scripts))


def test_reference_does_not_invent_negatives():
    ref = module["reference"]
    assert ref({1}, {51}, 1) == "explicit_normal_control"
    assert ref({1, 51}, {51}, 1) == "ambiguous"
    assert ref({140}, {51}, 1) == "unknown"
    assert ref({30, 51}, {51}, 1) == "positive"


def test_ranking_ties_and_missing_polarity():
    rank = module["rank_metrics"]
    assert rank([(0, True), (0, False)])["auroc"] == .5
    assert rank([(0, True), (0, False)])["average_precision"] == .5
    assert rank([(2, True), (-1, False)])["auroc"] == 1
    assert rank([(2, True)])["average_precision"] is None
    with pytest.raises(ValueError, match="nonfinite"):
        rank([(float("nan"), True)])
