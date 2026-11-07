import hashlib
import json
from pathlib import Path

OUTPUTS = Path(__file__).resolve().parents[2] / "outputs/results/revision_replay_diagnostics_20261107"


def _report(name):
    return json.loads((OUTPUTS / name).read_bytes())


def test_evidence_fingerprints_and_numerical_limits():
    for name, entry in _report("receipt.json")["outputs"].items():
        assert hashlib.sha256((OUTPUTS / name).read_bytes()).hexdigest() == entry["sha256"]
    residuals = _report("score_residuals.json")
    assert sum(p["score"]["above_historical_atol"] for p in residuals["P4"].values()) == 836
    assert sum(p["decision_changes"] for p in residuals["P4"].values()) == 0
    assert residuals["P6"]["top1_changes"] == residuals["P6"]["changes_with_same_top_two_candidates"] == 1
    assert residuals["P8"]["top1_changes"] == 0
    assert residuals["historical_pipeline_equivalence_claimed"] is False


def test_probe_and_official_fold_are_not_historical_reconstruction():
    probe = _report("p4_batch_probe.json")
    assert probe["records"] == 733 and probe["weights_or_thresholds_modified"] is False
    variants = probe["against_archived_panel_probabilities"]
    assert all(report["decision_disagreements"] == 0 and
               report["meets_historical_tolerance_on_all_panel_pairs"] is False
               for report in variants.values())
    comparisons = probe["comparisons_all_four_scores"]
    assert all(panel["score"]["max_absolute_difference"] == 0
               for panel in comparisons["same_batch_repeat"].values())
    assert sum(panel["decision_changes"] for panel in comparisons["batch32_vs_batch1"].values()) == 1
    fold = _report("p4_official_fold_coverage.json")
    assert fold["official_folds"]["10"]["ecgs"] == 2198
    assert fold["selected_p4"]["ecgs"] + fold["official_fold10_not_in_selected_p4"]["ecgs"] == 2198
    assert fold["selected_patient_overlap_with_official_folds_1_to_9"] == 0
    assert fold["historical_checkpoint_training_isolation_established"] is False
