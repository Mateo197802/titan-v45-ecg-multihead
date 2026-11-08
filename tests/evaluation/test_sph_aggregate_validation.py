import copy

import pytest

from scripts.external_validation.validate_sph_aggregate import validate_report


def _fixture():
    protocol = {"expected_source_records": 4, "classes": {"P6": ["AF"]},
                "endpoints": [{"profile": "P6", "name": "AF"}],
                "bootstrap": {"replicates": 10}}
    metrics = {"tp": 1, "tn": 1, "fp": 1, "fn": 0, "rows": 3,
               "accuracy": 2 / 3, "precision": 0.5, "recall": 1.0,
               "specificity": 0.5, "f1": 2 / 3, "auroc": 0.75,
               "average_precision": 0.5, "brier_score": 0.2, "ece": 0.3}
    report = {"schema": "TITAN_V45_SPH_ENDPOINT_RESULTS_V1",
              "full_population_flow": {"source_metadata_records": 4, "scored_records": 3,
                                       "status_counts": {"scored": 3, "technical_exclusion": 1}},
              "profile_flow": {"P6": {"source_records": 4, "scored_records": 3, "coverage": 0.75}},
              "endpoints": {"P6:AF": {"source_records": 4, "source_statement_positive": 2,
                            "source_statement_negative": 2, "scored_evaluable_records": 3,
                            "unscored_source_records": 1, "scored_positive": 1, "scored_negative": 2,
                            "metrics": metrics, "cluster_bootstrap_ci95": {
                                "_design": {"replicates": 10},
                                "accuracy": {"low": 0.4, "high": 0.9, "valid_replicates": 10,
                                             "invalid_replicates": 0}}}}}
    return report, protocol


def test_validator_reconciles_aggregate_without_record_data():
    report, protocol = _fixture()
    assert validate_report(report, protocol)["endpoints_checked"] == 1
    broken = copy.deepcopy(report)
    broken["endpoints"]["P6:AF"]["metrics"]["tp"] = 2
    with pytest.raises(ValueError, match="denominator|supports"):
        validate_report(broken, protocol)
    broken = copy.deepcopy(report)
    broken["endpoints"]["P6:AF"]["cluster_bootstrap_ci95"]["accuracy"]["valid_replicates"] = 9
    with pytest.raises(ValueError, match="bootstrap count"):
        validate_report(broken, protocol)
