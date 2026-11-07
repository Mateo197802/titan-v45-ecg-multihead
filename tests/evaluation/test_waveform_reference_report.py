import pytest

from titan_v45.evaluation.waveform_reference import compare_binary_panel, summarize_selected_union


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
