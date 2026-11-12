import runpy
import sys
from pathlib import Path
from types import SimpleNamespace

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


def test_inline_loader_still_exercises_perturbation_and_restores_hook():
    def prepare(record, morph):
        return record, morph(record, fs=125)

    owner = SimpleNamespace(prepare_p4_record=prepare)
    calls = [0]
    with module["perturb_preparation"](owner, "prepare_p4_record", calls):
        _, vector = owner.prepare_p4_record("record", lambda *a, **kw: np.ones(10))
        assert np.count_nonzero(vector) == 0
    assert owner.prepare_p4_record is prepare
    assert calls == [1]


def test_p6_intended_rows_do_not_include_p8_only_records():
    a, b, c = ("source", "A"), ("source", "B"), ("source", "C")
    scored = {"scores": {"AFIB": 0.5}, "labels": [], "top1": "AFIB", "used_fallback": False}
    rows = {a: {"P6": scored, "P8": scored}, b: {}, c: {"P8": scored}}
    report = module["compare"](rows, rows, "rhythm", {a, b})
    assert report["P6"]["intended_records"] == 2
    assert report["P6"]["ledger_universe_records"] == 3
    assert report["P6"]["paired_scored"] == 1
    assert report["P8"]["intended_records"] == 3
    with pytest.raises(ValueError, match="outside P6"):
        module["compare"](rows, rows, "rhythm", {b, c})
