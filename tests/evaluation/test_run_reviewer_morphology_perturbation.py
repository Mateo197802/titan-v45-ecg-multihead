import runpy
import sys
from pathlib import Path

import numpy as np
import pytest

scripts = Path(__file__).resolve().parents[2] / "scripts/evaluation"
sys.path.insert(0, str(scripts))
try:
    module = runpy.run_path(str(scripts / "run_reviewer_morphology_perturbation.py"))
finally:
    sys.path.remove(str(scripts))


def test_intervention_preserves_shape_dtype_and_calls_extractor():
    calls = [0]
    zero = module["neutralize"](lambda _: np.ones(10, dtype=np.float32), calls)
    output = zero(None)
    assert output.dtype == np.float32 and output.shape == (10,)
    assert np.count_nonzero(output) == 0 and calls == [1]
    invalid = module["neutralize"](lambda _: np.ones(11), calls)
    with pytest.raises(ValueError, match="contract"):
        invalid(None)


def test_comparison_preserves_unscored_rows_in_denominator():
    old = {("a", "1"): {"primary_scores": {"x": .7}, "pathology": {"x": True}}, ("a", "2"): {}}
    new = {("a", "1"): {"primary_scores": {"x": .4}, "pathology": {"x": False}}, ("a", "2"): {}}
    output = module["compare"](old, new, "pathology_primary4")["P4"]
    assert output["intended_records"] == 2 and output["paired_scored"] == 1
    assert output["decision_changes"] == 1
    assert output["by_class"]["x"]["max_absolute_delta"] == pytest.approx(.3)
    with pytest.raises(ValueError, match="universe"):
        module["compare"](old, {}, "pathology_primary4")
