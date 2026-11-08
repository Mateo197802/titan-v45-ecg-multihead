import pytest

from scripts.external_validation.plot_sph_aggregate import plot_sph_aggregate


def _metric(value):
    return value, {"low": value - 0.1, "high": value + 0.1}


def _report():
    endpoints = {}
    profiles = {name: {"coverage": 0.75, "scored_records": 3, "source_records": 4}
                for name in ("P6", "P8", "P4")}
    for profile in ("P6", "P8", "P4"):
        point, ci = _metric(0.8)
        endpoints[f"{profile}:TEST"] = {
            "scored_positive": 1,
            "scored_negative": 2,
            "metrics": {"sensitivity": point, "specificity": point, "auroc": point, "f1": point},
            "cluster_bootstrap_ci95": {
                "sensitivity": ci, "specificity": ci, "auroc": ci, "f1": ci,
            },
            "discordant_exact_duplicate_sensitivity": {
                "metrics": {"f1": 0.7},
                "cluster_bootstrap_ci95": {"f1": {"low": 0.6, "high": 0.8}},
            },
        }
    return {
        "schema": "TITAN_V45_SPH_ENDPOINT_RESULTS_V1",
        "full_population_flow": {
            "source_metadata_records": 4,
            "archive_records": 4,
            "technical_exclusions": 0,
            "inference_failures": 1,
            "missing_signal": 0,
        },
        "profile_flow": profiles,
        "endpoints": endpoints,
    }


def test_aggregate_plotter_writes_fixed_privacy_safe_figures(tmp_path):
    pytest.importorskip("matplotlib")
    result = plot_sph_aggregate(_report(), tmp_path)

    assert result["matplotlib_version"]
    assert set(result["files"]) == {
        "sph_profile_coverage.png", "sph_profile_coverage.pdf",
        "sph_endpoint_metrics.png", "sph_endpoint_metrics.pdf",
        "sph_duplicate_sensitivity.png", "sph_duplicate_sensitivity.pdf",
    }
    assert all((tmp_path / name).stat().st_size > 0 for name in result["files"])


def test_aggregate_plotter_rejects_nonaggregate_input(tmp_path):
    with pytest.raises(ValueError, match="schema"):
        plot_sph_aggregate({"schema": "private-ledger"}, tmp_path)
