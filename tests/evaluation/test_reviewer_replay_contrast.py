import importlib
import json
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts" / "evaluation"


@pytest.fixture
def contrast(monkeypatch):
    monkeypatch.syspath_prepend(str(SCRIPTS))
    return importlib.import_module("reviewer_replay_contrast")


def test_native_repeat_keeps_score_drift_separate_from_decision(contrast):
    old = {("a", "1"): {"primary_scores": {"LVH": 0.6}, "pathology": {"LVH": False},
                        "pre": "pathology_only", "post": "quarantine_not_assessed"}}
    now = {k: {**v, "primary_scores": {"LVH": 0.61}} for k, v in old.items()}
    out = contrast.native_compare(old, now, "P4")
    assert out["comparisons"]["P4"]["decision_changes_by_field"] == {"pathology": 0}
    assert out["comparisons"]["P4"]["score_differences_by_class"]["LVH"]["above_historical_atol"] == 1
    with pytest.raises(ValueError, match="universe"):
        contrast.native_compare(old, {}, "P4")


def test_missing_score_is_not_decision_agreement(contrast):
    rows = [{"source": "A", "record_id": "1", "probability": "0.71", "predicted": "1", "threshold": "0.705"},
            {"source": "A", "record_id": "2", "probability": "0.72", "predicted": "1", "threshold": "0.705"}]
    now = {("a", "1"): {"primary_scores": {"LVH": 0.70}, "pathology": {"LVH": False}}, ("a", "2"): {}}
    out = contrast.pathology_archived(rows, now, "LVH", 0.705)
    assert (out["archived_rows"], out["matched_rows"], out["missing_scores"]) == (2, 1, 1)
    assert out["diagnostics"]["decision_changes"] == 1


def test_lineage_float_serialization_and_real_threshold_change(contrast, tmp_path):
    (tmp_path / "commit.txt").write_text("commit\n")
    aggregate = {"thresholds": {"ASMI": 0.6699999999999999, "LVH": 0.705, "IMI": 0.635, "ISC_": 0.595},
                 "manifest_sha256_lf": "manifest", "release_sha256": {"asset": "digest"},
                 "weights_or_thresholds_modified": False, "device": "cuda", "torch": "test",
                 "morphology_candidate_sha256_lf": "morph"}
    path = tmp_path / "aggregate.json"
    path.write_text(json.dumps(aggregate))
    args = (tmp_path, "P4", {"asset": "digest"}, {"pathology_primary4_panels.csv": "manifest"}, "commit")
    assert contrast.lineage(*args)["runner_commit"] == "commit"
    aggregate["thresholds"]["ASMI"] += 0.00001
    path.write_text(json.dumps(aggregate))
    with pytest.raises(ValueError, match="threshold"):
        contrast.lineage(*args)
