import pytest

from titan_v45.evaluation.ptbxl_fold_coverage import compare_fold_coverage


def test_distinguishes_unselected_records_from_historical_exclusions():
    rows = [{"ecg_id": "1", "patient_id": "11.0", "strat_fold": "10"},
            {"ecg_id": "2", "patient_id": "11.0", "strat_fold": "10"},
            {"ecg_id": "3", "patient_id": "12.0", "strat_fold": "9"}]
    report = compare_fold_coverage(rows, {"ASMI": ("ptbxl_1",), "LVH": ("ptbxl_1",)})
    assert report["selected_p4"] == {"ecgs": 1, "patients": 1, "panel_observations": 2}
    assert report["official_fold10_not_in_selected_p4"]["ecgs"] == 1
    assert report["official_fold10_not_in_selected_p4"]["patients_with_no_selected_ecg"] == 0
    assert report["selected_patient_overlap_with_official_folds_1_to_9"] == 0
    assert report["historical_exclusion_reasons_known"] is False
    with pytest.raises(ValueError, match="missing"):
        compare_fold_coverage(rows, {"ASMI": ("ptbxl_4",)})
    with pytest.raises(ValueError, match="outside"):
        compare_fold_coverage(rows, {"ASMI": ("ptbxl_3",)})


def test_cross_fold_patient_is_measured_not_assumed_absent():
    rows = [{"ecg_id": "1", "patient_id": "11.0", "strat_fold": "10"},
            {"ecg_id": "2", "patient_id": "11", "strat_fold": "2"}]
    report = compare_fold_coverage(rows, {"ASMI": ("ptbxl_1",)})
    assert report["patients_assigned_multiple_official_folds"] == 1
    assert report["selected_patient_overlap_with_official_folds_1_to_9"] == 1
    assert report["historical_checkpoint_training_isolation_established"] is False
