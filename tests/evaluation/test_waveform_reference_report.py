import csv
import json
from pathlib import Path

import pytest

from titan_v45.evaluation.waveform_reference import (
    build_waveform_reference_report,
    compare_binary_panel,
    summarize_selected_union,
)


def test_report_uses_only_joined_references_and_same_archived_subset():
    archived = [
        {"source": "S", "record_id": "1", "target": "1", "predicted": "1", "probability": "0.9"},
        {"source": "S", "record_id": "2", "target": "0", "predicted": "0", "probability": "0.1"},
    ]
    ledger = {("s", "1"): {"pathology": {"ASMI": False}, "primary_scores": {"ASMI": 0.4}},
              ("s", "2"): {"post": "no_scores"},
              ("s", "3"): {"pathology": {"ASMI": True}, "primary_scores": {"ASMI": 0.8}}}
    comparison, panel = compare_binary_panel(archived, ledger, "ASMI")
    assert comparison["archived_reference_rows"] == 2
    assert comparison["missing_score_rows"] == 1
    assert comparison["new"]["rows"] == comparison["archived_matched"]["rows"] == 1
    assert comparison["new"]["accuracy"] == 0
    assert comparison["archived_matched"]["accuracy"] == 1
    assert panel.keys == (("s", "1"),)


def test_duplicate_reference_and_incomplete_scored_row_fail_closed():
    row = {"source": "S", "record_id": "1", "target": "1", "predicted": "1", "probability": "0.9"}
    with pytest.raises(ValueError, match="duplicate"):
        compare_binary_panel([row, row], {}, "ASMI")
    with pytest.raises(ValueError, match="incomplete"):
        compare_binary_panel([row], {("s", "1"): {"pathology": {"ASMI": True}}}, "ASMI")


def test_selected_union_accounts_for_shared_keys_and_unscored_branch():
    key = ("s", "1")
    failed = ("t", "2")
    p4 = {key: {"pre": "pathology_only", "post": "quarantine_not_assessed"},
          failed: {"pre": "no_scores", "post": "no_scores"}}
    rhythm = {key: {"pre": "rhythm_only", "post": "quarantine_not_assessed"}}
    result = summarize_selected_union(p4, rhythm)
    assert result["inputs"] == 2
    assert result["exact_key_overlap"] == 1
    assert result["transitions"] == {"both->quarantine_not_assessed": 1, "no_scores->no_scores": 1}
    assert result["quarantine_rate_all_inputs"] is None


def test_whole_report_resolves_canonical_profiles_and_tracks_missing_scores(tmp_path):
    repo = Path(__file__).resolve().parents[2]
    base = repo / "data/manifests/external_dev"

    def write_ledger(name):
        path = tmp_path / f"{name}.jsonl"
        with (base / f"{name}.csv").open(encoding="utf-8", newline="") as handle:
            keys = sorted({(row["source"], row["record_id"]) for row in csv.DictReader(handle)})
        path.write_text("".join(json.dumps({"source": source, "record_id": record_id,
                                            "pre": "no_scores", "post": "no_scores"}) + "\n"
                                for source, record_id in keys), encoding="utf-8")
        return path

    report = build_waveform_reference_report(
        repo, pathology_ledger=write_ledger("pathology_primary4_panels"),
        rhythm_ledger=write_ledger("rhythm_primary8_records"), n_bootstrap=0,
    )
    assert report["selected_key_union"]["transitions"] == {"no_scores->no_scores": 2926}
    assert report["P6"]["missing_score_rows"] == 1643
    assert report["P8"]["missing_score_rows"] == 2193
    assert sum(panel["missing_score_rows"] for panel in report["P4"]["classes"].values()) == 962
    assert report["P4"]["bootstrap_new"] is None
