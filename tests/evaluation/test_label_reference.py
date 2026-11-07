import pytest

from titan_v45.evaluation.label_reference import audit_af_reference_rows


def test_af_reference_audit_counts_overlap_without_claiming_incident_af():
    rows = [{"record_id": "a", "source": "benchmark", "dx_codes": "164889003|426783006", "accepted_labels": "AFIB|NSR"},
            {"record_id": "b", "source": "benchmark", "dx_codes": "426783006", "accepted_labels": "NSR"}]
    report = audit_af_reference_rows(rows, reference_field="accepted_labels")
    assert report["all_af_flags_match_codes"] is True
    assert report["af_reference_positive"] == 1
    assert report["sources"][0]["af_and_nsr_code_overlap"] == 1
    assert report["incident_af_validated"] is False


def test_missing_codes_and_disagreement_do_not_count_as_verified():
    rows = [{"record_id": "a", "source": "x", "dx_codes": "", "accepted_labels": "AFIB"},
            {"record_id": "b", "source": "x", "dx_codes": "426783006", "accepted_labels": "AFIB"}]
    report = audit_af_reference_rows(rows, reference_field="accepted_labels")
    assert report["unresolved_code_rows"] == 1
    assert report["af_flag_mismatches"] == 1
    assert report["all_af_flags_match_codes"] is False


def test_duplicate_records_are_rejected():
    row = {"record_id": "a", "source": "x", "dx_codes": "164889003", "true_labels": "AFIB"}
    with pytest.raises(ValueError, match="duplicate"):
        audit_af_reference_rows([row, row], reference_field="true_labels")


def test_empty_input_never_establishes_full_verification():
    assert audit_af_reference_rows([], reference_field="true_labels")["all_af_flags_match_codes"] is False
