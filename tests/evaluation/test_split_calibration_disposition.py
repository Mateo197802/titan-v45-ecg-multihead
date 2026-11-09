from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def test_p6_recorded_thresholds_and_unverified_isolation():
    profile = load("configs/profiles/rhythm_primary6_diagnostic.json")
    lineage = load("outputs/results/revision_20261029/p6_calibration_lineage_summary.json")
    assert profile["classes"] == lineage["classes"]
    assert profile["thresholds"] == pytest.approx(lineage["thresholds"])
    assert lineage["internal_records"] == 192
    assert lineage["internal_window_count"] == 276
    assert lineage["split_independence_certified"] is False
    assert lineage["complete_historical_manifests_recovered"] is False


def test_p4_thresholds_agree_without_claiming_patient_isolation():
    profile = load("configs/profiles/pathology_primary4.json")
    internal = load("outputs/results/internal/pathology_primary4_calibration.json")
    assert [internal["thresholds"][name] for name in profile["classes"]] == profile["thresholds"]
    fold = load("outputs/results/revision_replay_diagnostics_20261107/p4_official_fold_coverage.json")
    assert fold["selected_patient_overlap_with_official_folds_1_to_9"] == 0
    assert fold["historical_checkpoint_training_isolation_established"] is False
    assert fold["historical_parent_population_recovered"] is False


def test_split_disposition_records_boundaries():
    doc = (ROOT / "docs/reviewer_closure/SPLIT_CALIBRATION_DISPOSITION.md").read_text(encoding="utf-8")
    for phrase in ("17315", "17296", "192 ECG", "276 windows", "676 patients", "not certified"):
        assert phrase in doc
