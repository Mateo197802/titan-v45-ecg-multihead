import importlib
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from titan_v45.evaluation.revision_report import binary_metrics

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts" / "evaluation"


@pytest.fixture
def contrast(monkeypatch):
    monkeypatch.syspath_prepend(str(SCRIPTS))
    return importlib.import_module("reviewer_population_contrast")


def test_normal_unknown_and_nonmatching_outputs_counted_not_dropped(contrast):
    refs = {k: SimpleNamespace(primary_codes=codes, patient="patient"+k) for k, codes in
            {"a": {50}, "b": {1}, "c": {1, 50}, "d": {51}, "e": {50, 51}, "f": {82}}.items()}

    def row(label, score):
        return {"status": "scored", "profiles": {"P6": {
            "labels": [label], "top1": label, "scores": {"AFIB": score, "1AVB": 1-score},
            "used_fallback": False,
        }}}

    rows = dict(zip(refs, (row("AFIB", 0.8), row("AFIB", 0.6), row("AFIB", 0.7), row("1AVB", 0.2),
                           {"status": "inference_failure"}, row("1AVB", 0.1)), strict=True))
    config = {"proxy_codes": {"P6": [82]}, "other_observable_codes": {"P6": [51]}, "normal_code": 1}
    flow, clusters, (y, pred, scores, restricted) = contrast.observe(
        rows, refs, dict(zip(refs, refs, strict=True)), "P6", ["AFIB"], [{50}], config)
    assert sum(v["metadata_ecgs"] for v in flow.values()) == 6
    assert flow["ambiguous_normal_and_other_statement"]["scoring_state"] == {"scored": 1}
    assert flow["out_of_profile_observable_no_mapped_statement"]["released_calls"] == {"1AVB": 1}
    assert flow["mapped_plus_other_statement"]["scoring_state"] == {"inference_failure": 1}
    assert clusters == ["a", "b", "d", "f"]
    assert restricted.tolist() == [True, False, False, False]
    result = contrast.point(y, pred, scores, np.ones(len(y), dtype=bool), ["AFIB"], binary_metrics)
    assert result["endpoints"]["AFIB"]["metrics"]["fp"] == 1
    assert result["endpoints"]["AFIB"]["metrics"]["npv"] == 1


def test_paired_denominator_effect_and_undefined_restricted_specificity(contrast):
    y = np.array([[1], [0], [0], [1]])
    pred = np.array([[1], [1], [0], [0]])
    out = contrast.paired_contrast(y, pred, np.array([True, False, False, True]), ["g", "g", "h", "h"],
                                   {"seed": 7, "replicates": 25, "level": 0.95})
    assert out[0]["restricted_minus_all"] == pytest.approx(2/3 - 0.5)
    assert out[2]["restricted_minus_all"] == 0
    assert out[3]["restricted_minus_all"] is None
    assert out[3]["invalid_replicates"] == 25
