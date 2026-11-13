import importlib
import json
from pathlib import Path

import pytest


@pytest.fixture
def verify(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts/evaluation"))
    return importlib.import_module("verify_reviewer_scientific_closure")


def inputs(verify):
    routes = {"accepted": 150, "abstained": 49, "technical_unscored": 1}
    score = {
        "source_archive_sha256": verify.ARCHIVE_SHA256, "protocol_sha256": verify.PROTOCOL_SHA256,
        "policy_sha256": verify.POLICY_SHA256, "eligible_ecgs": 200, "publisher_verified_waveform_files": 400,
        "reference_values_used": False, "route_reference_values_used": False, "routes": routes,
        "scored_by_profile": {p: {"scored": 199, "technical_unscored": 1} for p in ("P6", "P8", "P4")},
    }
    evaluated = {
        "scoring_receipt_sha256": "test-score-seal", "frozen_protocol_sha256": verify.PROTOCOL_SHA256,
        "frozen_policy_sha256": verify.POLICY_SHA256, "historical_quarantine": "WITHDRAW_HISTORICAL_CLAIM",
        "second_stage_or_human_review": False,
        "joint_selective": {
            "routes": routes, "denominator_all_eligible": 200, "denominator_scored_jointly": 199,
            "coverage_all_eligible": .75, "abstention_all_eligible": .245, "risk_baseline": .25,
            "risk_accepted": .2, "risk_abstained_counterfactual": .4,
            "opportunity_denominators": {"baseline": 40, "accepted": 30, "abstained_counterfactual": 10},
            "wrong_opportunities": {"baseline": 10, "accepted": 6, "abstained_counterfactual": 4},
        },
        "endpoints": {"P8:AFIB": {
            "estimates": {"all_eligible": {
                "eligible_ecgs": 200, "reference_states": {"positive": 2, "negative": 4, "unknown": 194},
                "known_scored_ecgs": 6, "descriptive_confusion": {"tn": 3, "fp": 1, "fn": 1, "tp": 1},
            }},
            "joint_positive_disposition": {"all_reference_positives": 2, "emitted_tp": 1,
                                           "abstained_positive_no_output": 1},
        }},
    }
    r = {"two_sided_monte_carlo_p": .2, "absolute_null_extremes": 1, "permutations": 9,
         "holm_adjusted_p": .6, "observed_delta_macro_f1": 0,
         "original_bootstrap_rederived": {"with_minus_without": 0}}
    morph = {"fit_or_feature_extraction_performed": False, "profiles": dict.fromkeys(("P6", "P8", "P4"), r)}
    sph = {
        "eligible_ecgs": 25770, "ecg_by_split": {"calibration": 12901, "held": 12869},
        "overlap_calibration_held": {"patient": 0, "signal": 0, "component": 0},
        "joint_policy_sha256": verify.POLICY_SHA256, "exact_calibration_recipe_rederived": True,
    }
    return score, evaluated, morph, sph, "test-score-seal"


def test_verifier_reconciles_opportunities_and_rejects_mislabeled_unknowns(verify):
    args = inputs(verify)
    verify.check_scientific(*args)
    args[1]["endpoints"]["P8:AFIB"]["estimates"]["all_eligible"]["known_scored_ecgs"] = 200
    with pytest.raises(ValueError, match="unknown references"):
        verify.check_scientific(*args)


def test_verifier_rejects_accepted_only_metric_with_inflated_denominator(verify):
    args = inputs(verify)
    args[1]["joint_selective"]["risk_accepted"] = .15
    with pytest.raises(ValueError, match="wrong known-reference denominator"):
        verify.check_scientific(*args)


def test_verifier_recomputes_familywise_morphology_adjustment(verify):
    args = inputs(verify)
    args[2]["profiles"]["P8"] = {**args[2]["profiles"]["P8"], "holm_adjusted_p": .2}
    with pytest.raises(ValueError, match="morphology robustness"):
        verify.check_scientific(*args)


def test_ptbxl_support_has_all_eleven_dispositions_and_no_proxy_positives(verify):
    path = (Path(__file__).resolve().parents[2]
            / "outputs/results/reviewer_closure_experiments/ptbxl_other_support_verified_v2.json")
    audit = json.loads(path.read_bytes())
    verify.check_ptbxl_support(audit, verify.digest(path))
    part = audit["endpoint_support"]["LQTS"]["P4_scoreable"]
    for counts in part.values():
        counts["positive"] = counts.pop("non_equivalent_proxy")
    with pytest.raises(ValueError, match="proxy boundary"):
        verify.check_ptbxl_support(audit, verify.digest(path))


def test_native_ludb_group_routes_and_matched_contrasts_reconcile(verify):
    path = Path(__file__).resolve().parents[2] / "outputs/results/reviewer_closure_experiments"
    score = json.loads((path / "ludb_scoring_receipt.json").read_bytes())
    result = json.loads((path / "ludb_fixed_policy_and_reference_aggregate.json").read_bytes())
    verify.check_ludb_detail(score, result)
    result["matched_restricted_contrast"]["P4"]["means"]["all_eligible"]["f1"] = 0.0
    with pytest.raises(ValueError, match="contrast arithmetic"):
        verify.check_ludb_detail(score, result)


def test_native_ptb_diagnostic_only_counts_known_references_and_frozen_calls(verify):
    path = Path(__file__).resolve().parents[2] / "outputs/results/reviewer_closure_experiments"
    score_path = path / "ptb_diagnostic_scoring_receipt.json"
    score = json.loads(score_path.read_bytes())
    result = json.loads((path / "ptb_diagnostic_transport_aggregate.json").read_bytes())
    eligibility = json.loads((path / "ptb_diagnostic_eligibility_verified_v2.json").read_bytes())
    verify.check_ptb(score, result, eligibility, verify.digest(score_path))
    result["endpoints"]["ALMI"]["separately_trained_PTBXL_head"]["metrics"]["recall"] = 21 / 549
    with pytest.raises(ValueError, match="binary metrics or confusion counts"):
        verify.check_ptb(score, result, eligibility, verify.digest(score_path))
