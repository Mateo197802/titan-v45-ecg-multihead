import copy
import runpy
from pathlib import Path

import pytest

compare = runpy.run_path(
    str(Path(__file__).resolve().parents[2] / "scripts/evaluation/compare_reviewer_baseline.py")
)["compare"]


def scored():
    return {
        "status": "scored",
        "profiles": {
            p: {
                "labels": ["a"], "top1": "a", "used_fallback": False,
                "threshold_crossings": ["a"], "scores": {"a": 0.7},
                "auxiliary_scores": {"aux": 0.2},
            } for p in ("P6", "P8", "P4")
        },
    }


def test_decision_agreement_does_not_imply_score_equivalence():
    old = {"r": scored()}
    new = copy.deepcopy(old)
    new["r"]["profiles"]["P4"]["scores"]["a"] += 0.001
    result = compare(old, new, 1e-5)
    assert result["profiles"]["P4"]["decision_disagreements"] == 0
    assert result["profiles"]["P4"]["scores"]["above_tolerance"] == 1
    assert not result["strict_equivalence"]
    assert compare(old, old, 1e-5)["strict_equivalence"]


def test_missing_signal_is_not_equivalent():
    rows = {"r": {"status": "missing_signal"}}
    assert not compare(rows, rows, 1e-5)["strict_equivalence"]
    with pytest.raises(ValueError, match="record universes"):
        compare(rows, {}, 1e-5)
