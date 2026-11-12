import importlib
from pathlib import Path

import pytest


@pytest.fixture
def renderer(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts/evaluation"))
    return importlib.import_module("render_reviewer_closure_tables")


def test_one_polarity_has_descriptive_sensitivity_but_not_specificity(renderer):
    row = {
        "eligible_ecgs": 200, "reference_states": {"positive": 5, "unknown": 195},
        "known_scored_ecgs": 5, "descriptive_confusion": {"tp": 2, "fn": 3, "fp": 0, "tn": 0},
        "positive_reference_sensitivity": 0.4, "status": "one_reference_polarity_only",
    }
    assert renderer.estimates(row) == (
        200, "positive: 5; unknown: 195", 5, "2/3/0/0", "0.4000",
        "NA", "NA", "NA", "NA", "NA", "NA", "one_reference_polarity_only",
    )


def test_rank_only_has_no_binary_call(renderer):
    row = {
        "eligible_ecgs": 549, "reference_states": {"positive": 50, "negative": 80, "unknown": 419},
        "known_scored_ecgs": 130, "ranking": {"auroc": 0.4, "average_precision": 0.3}, "status": "rank_only",
    }
    assert renderer.estimates(row)[3:] == ("NA", "NA", "NA", "NA", "NA", "NA", "0.4000", "0.3000", "rank_only")


def test_route_error_denominators_are_distinct(renderer):
    d = {
        "routes": {"accepted": 152, "abstained": 48},
        "denominator_all_eligible": 200,
        "denominator_scored_jointly": 200,
        "opportunity_denominators": {"baseline": 600, "accepted": 450, "abstained_counterfactual": 150},
        "wrong_opportunities": {"baseline": 180, "accepted": 145, "abstained_counterfactual": 35},
        "coverage_all_eligible": 0.76, "abstention_all_eligible": 0.24,
        "risk_baseline": 180 / 600, "risk_accepted": 145 / 450, "risk_abstained_counterfactual": 35 / 150,
        "aurc_scored": 0.31,
    }
    d["cluster_intervals"] = {key: {"bounds": [0.2, 0.4], "valid": 2000} for key in d}
    ludb = {
        "joint_selective": d, "routing_by_principal_rhythm": {}, "endpoints": {},
        "matched_restricted_contrast": {}, "matched_selective_contrast": {"means": {}},
    }
    rendered = "\n".join(renderer.render_ludb(ludb))
    assert "152 / 200 ECGs" in rendered
    assert "145 / 450 endpoint opportunities" in rendered
    assert "35 / 150 endpoint opportunities" in rendered
    assert "No referral or human review" in rendered
