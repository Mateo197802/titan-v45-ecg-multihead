import importlib
import json
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def closure(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts/evaluation"))
    return importlib.import_module("evaluate_reviewer_closure_ludb")


def test_references_preserve_unknown_and_exclude_non_equivalences(closure):
    rules = json.loads((ROOT / "configs/reviewer_experiments/scientific_closure_v1.json").read_bytes())["reference_rules"]
    states, rhythm = closure.reference_states({
        "Rhythms": "sinus rhythm", "Conduction abnormalities": "Incomplete LBBB; III degree AV-block",
        "Extrasystolies": "Atrial extrasystole, type: single PAC",
        "Cardiac pacing": "", "Hypertrophies": "Left atrial overload; Left ventricular hypertrophy",
    }, rules)
    assert rhythm == "NSR"
    assert states["NSR"] == states["PAC"] == states["3AVB"] == states["LVH"] == "positive"
    assert states["AFIB"] == states["Flutter"] == "negative"
    assert all(states[key] == "unknown" for key in ("LBBB", "RBBB", "LAE", "LQTS", "Paced", "ALMI", "2AVB"))
    assert states["P8_Other_mapped"] == "positive"
    states, rhythm = closure.reference_states({
        "Rhythms": "atrial fibrillation; uncertain descriptor", "Conduction abnormalities": "",
        "Extrasystolies": "", "Cardiac pacing": "", "Hypertrophies": "",
    }, rules)
    assert rhythm is None and states["AFIB"] == states["P6_Other_mapped"] == "unknown"


def test_risk_coverage_groups_ties_and_preserves_unknown_opportunities(closure):
    c, r, a = closure.risk_curve(np.array([.2, .1, .2]), np.array([1, 1, 0]),
                                 np.array([2, 2, 0]), np.ones(3, dtype=int))
    assert c == [2 / 3, 1.0] and r == [.5, .5] and a == .5
    c, r, a = closure.risk_curve(np.array([.2, .1]), np.array([0, 1]),
                                 np.array([0, 2]), np.ones(2, dtype=int))
    assert c == [.5, 1.0] and r == [None, .5] and a is None


def test_positive_disposition_does_not_count_abstained_positives_as_emitted_errors(closure):
    rows = [{"key": str(i), "route": {"state": state}, "profiles": {"P8": {"labels": labels}}}
            for i, (state, labels) in enumerate((
                ("accepted", ["AFIB"]), ("accepted", []), ("abstained", []), ("technical_unscored", [])))]
    refs = {r["key"]: {"AFIB": "positive"} for r in rows}
    assert closure.disposition(rows, refs, "P8", "AFIB") == {
        "emitted_tp": 1, "emitted_fn": 1, "abstained_positive_no_output": 1,
        "abstained_baseline_counterfactual_fn": 1, "technical_unscored_positive_no_output": 1,
        "all_reference_positives": 4,
    }
