from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_archived_replay_stages_and_prespecified_tolerance():
    path = ROOT / "outputs/results/revision_20261029/p4_replay_stage_summary.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["legacy_candidate_decision_disagreements"] == 166
    stages = {stage["slurm_job_id"]: stage for stage in data["stages"]}
    assert stages["31577"]["decision_disagreements"] == 168
    for job in ("31604", "31605"):
        assert stages[job]["records"] == 733
        assert stages[job]["panel_rows"] == 962
        assert stages[job]["decision_disagreements"] == 0
        assert stages[job]["max_absolute_probability_difference"] > 1e-5
        assert stages[job]["selected_cohort_equivalence_passed"] is False
    assert data["criterion_not_relaxed_after_results"]["probability_atol"] == 1e-5
    assert data["criterion_not_relaxed_after_results"]["probability_rtol"] == 0.0
    assert data["strict_probability_replay_resolved"] is False
    assert data["historical_complete_preprocessing_source_recovered"] is False


def test_later_replay_results_and_earlier_stages_are_not_conflated():
    p4 = json.loads((ROOT / "outputs/results/revision_20261107/pathology_waveform.json").read_text())
    assert p4["quarantine_rate_all_inputs"] is None
    doc = (ROOT / "docs/reviewer_closure/REPLAY_EQUIVALENCE_DISPOSITION.md").read_text(encoding="utf-8")
    for item in ("fc8d7367f9f2c108376839435021ec3172fe2757faa4a615f0ef5d39cbf1e855",
                 "31577", "31604", "31605", "32448", "32576", "836/962", "1e-5"):
        assert item in doc
