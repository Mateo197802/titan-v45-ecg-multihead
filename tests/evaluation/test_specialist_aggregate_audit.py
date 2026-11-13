import csv
import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[2] / "scripts" / "specialist_experiments"))
from verify_aggregate_results import verify_aggregate_results  # noqa: E402

CLASS_FIELDS = [
    "profile", "scope", "source", "model", "endpoint", "estimable", "rows", "n_ecg",
    "n_groups", "positive_support", "negative_support", "predicted_positive_support",
    "tp", "tn", "fp", "fn", "accuracy", "precision", "recall", "specificity", "f1",
    "negative_predictive_value",
]
SUMMARY_FIELDS = [
    "profile", "scope", "source", "model", "evaluable_endpoints",
    "model_evaluable_endpoints", "comparison_endpoints", "macro_f1",
    "baseline_macro_f1", "delta_macro_f1_vs_baseline",
]


def _write_csv(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as destination:
        writer = csv.DictWriter(destination, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _fixture_tables(tmp_path):
    per_class = tmp_path / "per_class.csv"
    comparison = tmp_path / "comparison.csv"
    common = {"profile": "P4", "scope": "internal", "source": "ptbxl", "endpoint": "ASMI",
              "estimable": "true", "rows": "4", "n_ecg": "4", "n_groups": "4",
              "positive_support": "2", "negative_support": "2"}
    class_rows = [
        {**common, "model": "published_baseline", "predicted_positive_support": "1", "tp": "1",
         "tn": "2", "fp": "0", "fn": "1", "accuracy": "0.75", "precision": "1",
         "recall": "0.5", "specificity": "1", "f1": str(2 / 3),
         "negative_predictive_value": str(2 / 3)},
        {**common, "model": "candidate", "predicted_positive_support": "2", "tp": "2",
         "tn": "2", "fp": "0", "fn": "0", "accuracy": "1", "precision": "1",
         "recall": "1", "specificity": "1", "f1": "1", "negative_predictive_value": "1"},
    ]
    _write_csv(per_class, CLASS_FIELDS, class_rows)
    summaries = [
        {"profile": "P4", "scope": "internal", "source": "ptbxl", "model": "published_baseline",
         "evaluable_endpoints": "1", "model_evaluable_endpoints": "1", "comparison_endpoints": "['ASMI']",
         "macro_f1": str(2 / 3), "baseline_macro_f1": str(2 / 3), "delta_macro_f1_vs_baseline": "0"},
        {"profile": "P4", "scope": "internal", "source": "ptbxl", "model": "candidate",
         "evaluable_endpoints": "1", "model_evaluable_endpoints": "1", "comparison_endpoints": "['ASMI']",
         "macro_f1": "1", "baseline_macro_f1": str(2 / 3), "delta_macro_f1_vs_baseline": str(1 / 3)},
    ]
    _write_csv(comparison, SUMMARY_FIELDS, summaries)
    return per_class, comparison


def test_aggregate_audit_recomputes_metrics_and_summary(tmp_path):
    per_class, comparison = _fixture_tables(tmp_path)

    receipt = verify_aggregate_results(per_class, comparison)

    assert receipt["status"] == "PASS"
    assert receipt["confusion_metric_rows_verified"] == 2
    assert receipt["macro_f1_rows_verified"] == 2
    assert receipt["baseline_delta_rows_verified"] == 1
    assert receipt["identifier_like_columns"] == []


def test_aggregate_audit_rejects_identifier_columns(tmp_path):
    per_class, comparison = _fixture_tables(tmp_path)
    fields = CLASS_FIELDS + ["patient_id"]
    rows = list(csv.DictReader(per_class.open(newline="", encoding="utf-8")))
    _write_csv(per_class, fields, rows)

    with pytest.raises(ValueError, match="identifier-like columns"):
        verify_aggregate_results(per_class, comparison)


def test_aggregate_audit_rejects_inconsistent_confusion_counts(tmp_path):
    per_class, comparison = _fixture_tables(tmp_path)
    rows = list(csv.DictReader(per_class.open(newline="", encoding="utf-8")))
    rows[0]["tp"] = "0"
    _write_csv(per_class, CLASS_FIELDS, rows)

    with pytest.raises(ValueError, match="confusion counts"):
        verify_aggregate_results(per_class, comparison)


def test_published_split_denominators_are_consistent():
    split_path = (
        Path(__file__).parents[2]
        / "outputs"
        / "results"
        / "specialist_heads"
        / "20261111-v2"
        / "SPECIALIST_DATASET_SPLITS.json"
    )
    splits = json.loads(split_path.read_text(encoding="utf-8"))
    rhythm = splits["rhythm"]
    rhythm_source_records = sum(
        source["included_records"] for source in rhythm["sources"].values()
    )
    assert rhythm_source_records == rhythm["included_records_scored"] == 11133
    assert sum(rhythm["sources"]["chapman_shaoxing"]["split_records"].values()) == 8355
    assert sum(rhythm["sources"]["cpsc2018"]["split_records"].values()) == 1681
    assert sum(rhythm["sources"]["georgia"]["split_records"].values()) == 1097

    pathology = splits["pathology"]
    assert sum(pathology["split_records"].values()) == pathology["included_records"] == 6205
    assert pathology["fold_10_used"] is False
    assert splits["privacy_and_scope"]["independent_external_validation"] == "NOT_RUN"

    chapman = rhythm["sources"]["chapman_shaoxing"]
    excluded = (
        chapman["excluded_prior_v45_evaluation_records"]
        + chapman["excluded_byte_identical_previous_v45_evaluation_waveforms"]
        + chapman["excluded_other_byte_identical_waveform_duplicates"]
        + chapman["excluded_invalid_wfdb_headers"]
    )
    assert chapman["candidate_records"] - chapman["included_records"] == excluded


def test_public_reproducibility_manifest_hashes_match_artifacts():
    output_dir = (
        Path(__file__).parents[2]
        / "outputs"
        / "results"
        / "specialist_heads"
        / "20261111-v2"
    )
    manifest = json.loads(
        (output_dir / "SPECIALIST_REPRODUCIBILITY_MANIFEST.json").read_text(encoding="utf-8")
    )
    for filename, item in manifest["public_aggregate_artifacts"].items():
        content = (output_dir / filename).read_bytes()
        expected_hash = item.get("public_lf_normalized_sha256", item.get("sha256"))
        expected_size = item.get("public_lf_normalized_bytes", item.get("public_bytes"))
        assert hashlib.sha256(content).hexdigest() == expected_hash
        assert len(content) == expected_size
