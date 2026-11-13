import runpy
import sys
from pathlib import Path

import numpy as np
import pytest

scripts = Path(__file__).resolve().parents[2] / "scripts/evaluation"
sys.path.insert(0, str(scripts))
try:
    module = runpy.run_path(str(scripts / "evaluate_reviewer_selective_policy.py"))
finally:
    sys.path.remove(str(scripts))


def test_risk_curve_ties_and_auc():
    curve = module["curve"]
    c, r, area = curve(np.array([.8, .8, .2]), np.array([0, 1, 1]))
    assert c == pytest.approx([2/3, 1])
    assert r == pytest.approx([.5, 2/3])
    assert area == pytest.approx(5/9)


def test_route_ignores_references_and_keeps_technical_state():
    route = module["route_record"]
    profiles = module["PROFILES"]
    row = {"status": "scored", "reference": {"ignored": True},
           "profiles": {p: {"scores": {"a": .6}} for p in profiles}}
    thresholds = {p: {"a": .5} for p in profiles}
    cutoffs = dict(zip(profiles, [.05, .2, .05], strict=True))
    routed = route(row, thresholds, cutoffs)
    assert [routed[p]["route"] for p in profiles] == ["accepted", "abstained", "accepted"]
    row["reference"] = None
    assert routed == route(row, thresholds, cutoffs)
    assert all(v["route"] == "not_scored" for v in route({"status": "missing_signal"}, {}, {}).values())


def test_endpoint_route_counts_and_private_safe_aggregate():
    summarize = module["profile_stats"]
    rows = [{"component": str(i), "route": route, "confidence": c,
             "reference": [y], "decision": [d], "scores": [float(d)]}
            for i, (route, c, y, d) in enumerate([
                ("accepted", .8, 1, 1), ("accepted", .9, 0, 0),
                ("abstained", .1, 1, 0), ("not_scored", 0, 1, 0),
            ])]
    summary = summarize(rows, ["endpoint"], lambda *a: {}, {"replicates": 20, "seed": 1, "level": .95})
    assert summary["coverage_all_held"] == .5
    assert summary["coverage_scored"] == pytest.approx(2/3)
    assert summary["abstention_all_held"] == .25
    assert summary["endpoints"]["endpoint"]["routes"]["abstained"]["fn"] == 1
    assert summary["endpoints"]["endpoint"]["held_statement_positive"] == 3
    assert summary["macro_f1"]["baseline"] == pytest.approx(2/3)
    assert summary["macro_f1"]["accepted"] == 1
    assert len(summary["risk_coverage_curve"]["risk"]) == 100
