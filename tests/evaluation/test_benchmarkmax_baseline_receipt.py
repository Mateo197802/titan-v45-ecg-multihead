import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_observed_baseline_diagnostic_is_aggregate_and_reconciles():
    path = ROOT / "outputs/results/benchmarkmax/sph_baseline_diagnostic_32726.json"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == (
        "248b4857cbd4a92ad42bc96d78dab9f6431a0d572f9325684b520c31e27670c6"
    )
    text = path.read_text(encoding="utf-8")
    result = json.loads(text)
    assert result["source_records"] == 25770 and result["source_patients"] == 24666
    assert result["individual_records_exported"] is False
    assert not re.search(r'"A[0-9]{5}"|"(?:record_id|patient_id|ecg_id)"|/home/', text)
    assert set(result["endpoints"]) == {"P6:AFIB", "P8:PAC", "P4:ASMI", "P4:LVH", "P4:IMI"}
    for endpoint in result["endpoints"].values():
        bins = endpoint["score_bins_uniform_20"]
        counts = endpoint["frozen_decisions"]
        assert len(bins) == 20
        assert sum(item["positive"] for item in bins) == counts["tp"] + counts["fn"]
        assert sum(item["negative"] for item in bins) == counts["tn"] + counts["fp"]
        assert sum(counts.values()) == endpoint["records"] == 25770
        assert endpoint["statement_prevalence"] == endpoint["positive_statements"] / endpoint["records"]
        assert endpoint["average_precision_no_skill_baseline"] == endpoint["statement_prevalence"]
        assert len(endpoint["exploratory_binned_threshold_curve"]) == 20


def test_diagnostic_table_values_are_derived_from_the_aggregate():
    path = ROOT / "outputs/results/benchmarkmax/sph_baseline_diagnostic_32726.json"
    result = json.loads(path.read_text(encoding="utf-8"))
    document = (ROOT / "docs/benchmarkmax/OBSERVED_SPH_BASELINE.md").read_text(encoding="utf-8")
    for name, endpoint in result["endpoints"].items():
        counts = endpoint["frozen_decisions"]
        ppv = counts["tp"] / (counts["tp"] + counts["fp"])
        row = (f"| {name.replace(':', ' ')} | {endpoint['statement_prevalence']:.2%} | "
               f"{counts['tp']:,} | {counts['fp']:,} | {counts['fn']:,} | {ppv:.2%} | "
               f"{endpoint['frozen_auroc']:.4f} | {endpoint['frozen_average_precision']:.4f} | "
               f"{endpoint['frozen_brier']:.4f} | {endpoint['frozen_ece']:.4f} |")
        assert row in document


def test_benchmarkmax_status_documents_reflect_completed_b1_calibration():
    feasibility = (ROOT / "docs/benchmarkmax/DATA_AND_LABEL_FEASIBILITY_REPORT.md").read_text(
        encoding="utf-8"
    )
    baseline = (ROOT / "docs/benchmarkmax/OBSERVED_SPH_BASELINE.md").read_text(
        encoding="utf-8"
    )
    readme = (ROOT / "docs/benchmarkmax/README.md").read_text(encoding="utf-8")
    feasibility_flat = " ".join(feasibility.split())

    assert "B1 calibration diagnostic was completed" in feasibility_flat
    assert "not a trained candidate model or independent validation" in feasibility_flat
    assert "B1_SPH_CALIBRATION_RESULTS.md" in feasibility
    assert "B1_SPH_CALIBRATION_RESULTS.md" in baseline
    assert "SPH_SCALE_SENSITIVITY_RESULTS.md" in feasibility
    assert "No V4.6\ncheckpoint or trained specialist exists yet." in baseline
    assert "B1_SPH_CALIBRATION_RESULTS.md" in readme
    assert "SPH_SCALE_SENSITIVITY_RESULTS.md" in readme


def test_scale_sensitivity_registry_records_completed_probe():
    registry = json.loads(
        (ROOT / "docs/benchmarkmax/BENCHMARKMAX_EXPERIMENT_REGISTRY.json").read_text(
            encoding="utf-8"
        )
    )
    experiment = next(
        item
        for item in registry["experiments"]
        if item["id"] == "B1-SPH-AMPLITUDE-SENSITIVITY"
    )

    assert experiment["status"] == "completed_label_blind_diagnostic"
    assert experiment["cedia_job"] == 32761
    assert experiment["aggregate_sha256"] == (
        "63c03aabb91d9507ee19151b27a320c2c6faa4471f8eda1d2dccb33f4fa8c694"
    )
    assert experiment["result_document"] == "SPH_SCALE_SENSITIVITY_RESULTS.md"


def test_scale_sensitivity_result_document_matches_aggregate():
    result = json.loads(
        (ROOT / "outputs/results/benchmarkmax/sph_scale_sensitivity_32761.json").read_text(
            encoding="utf-8"
        )
    )
    document = (ROOT / "docs/benchmarkmax/SPH_SCALE_SENSITIVITY_RESULTS.md").read_text(
        encoding="utf-8"
    )
    for factor in ("0.5", "2.0"):
        for profile, profile_result in result["perturbations_vs_factor_1"][factor]["profiles"].items():
            assert profile_result["top1_changes"] == 0
            assert profile_result["fallback_changes"] == 0
            for change in profile_result["score_changes"].values():
                assert change["mean_absolute"] == 0
                assert change["max_absolute"] == 0
                assert change["label_changes"] == 0
            class_outputs = len(profile_result["score_changes"]) * result["selected_records"]
            row = f"| `{factor}x` | `{profile}` | 0 | 0/{class_outputs} | 0/128 | 0/128 |"
            assert row in document

    for profile, profile_result in result["baseline_replay_vs_archived"]["profiles"].items():
        assert profile_result["top1_changes"] == 0
        assert profile_result["fallback_changes"] == 0
        assert sum(
            change["label_changes"] for change in profile_result["score_changes"].values()
        ) == 0
        max_difference = max(
            change["max_absolute"] for change in profile_result["score_changes"].values()
        )
        row = f"| {profile} | {max_difference:.6e} | 0 | 0 | 0 |"
        assert row in document

    assert result["selected_records"] == 128
    assert "32761" in document
    assert "63c03aabb91d9507ee19151b27a320c2c6faa4471f8eda1d2dccb33f4fa8c694" in document
