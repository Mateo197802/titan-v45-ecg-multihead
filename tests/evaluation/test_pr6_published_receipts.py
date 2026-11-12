import csv
import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "outputs/results/external_validation_20261111"
FIRST = RESULTS / "code15-first"
FULL = RESULTS / "code15-full"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def test_first_code_archive_custody_and_aggregate_conservation():
    receipt_path = FIRST / "code15_evaluation_receipt.json"
    receipt = load(receipt_path)
    audit = load(RESULTS / "PATIENT_SPLIT_AND_OVERLAP_AUDIT.json")["code15"]
    lineage = load(RESULTS / "EXPERIMENT_AND_CHECKPOINT_LINEAGE.json")
    assert audit["paired_evaluation_receipt_sha256"] == sha256(receipt_path)
    assert lineage["code15"]["first_paired_receipt_sha256"] == sha256(receipt_path)
    assert receipt["protocol_sha256"] == sha256(ROOT / "docs/external_validation_20261111/FROZEN_CODE15_PROTOCOL.json")
    assert receipt["aggregate_csv_sha256"] == sha256(FIRST / "CODE15_PER_CLASS.csv")
    for filename, expected in receipt["aggregate_views_sha256"].items():
        assert sha256(FIRST / filename) == expected
    assert not receipt["complete_archive_coverage"]
    assert receipt["historical_patient_independence"] == "NOT_CERTIFIED"
    assert receipt["point_estimates_independently_verified"]["metric_rows_verified"] == 20
    assert receipt["point_estimates_independently_verified"]["patient_bootstrap_replayed"]
    assert audit["duration_contract"] == "NOT_CERTIFIED"
    boundary = audit["signal_boundary_audit"]
    assert boundary["scored_nominal_48_48"] == 0
    assert boundary["scored_symmetric_581_581"] + boundary["scored_other_left_with_right_581"] == receipt["n_ecg"]
    counts = receipt["counts"]
    assert sum(counts[key] for key in ("unexpected_code_padding", "flat_lead",
                                       "short_or_ambiguous_code_duration")) + receipt["n_ecg"] == counts["selected_ecgs"]
    with (FIRST / "EXTERNAL_CODE15_RESULTS.csv").open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        assert {"exam_id", "patient_id", "record_id", "statement"}.isdisjoint(reader.fieldnames)
        rows = list(reader)
    assert len(rows) == 20
    assert len({(r["profile"], r["endpoint"], r["model"]) for r in rows}) == 20
    for row in rows:
        assert row["scope"] == "FIRST_ARCHIVE_ONLY_NO_PROMOTION"
        tp, tn, fp, fn = (int(row[key]) for key in ("tp", "tn", "fp", "fn"))
        assert tp + tn + fp + fn == int(row["n_ecg_with_reference"]) == receipt["n_ecg"]
        assert tp + fn == int(row["n_positive_ecg"])
        assert tn + fp == int(row["n_negative_ecg"])
        assert float(row["f1"]) == pytest.approx(2 * tp / (2 * tp + fp + fn))
    for decision in receipt["promotion"].values():
        assert decision["decision"] == "INCOMPLETE_NO_PROMOTION"
        assert not decision["observed_metric_gate_pass"]


def test_full_code_delivery_matches_cedia_hashes_and_frozen_decisions():
    evaluation_path = FULL / "code15_evaluation_receipt.json"
    delivery_path = FULL / "CODE15_FULL_DELIVERY_RECEIPT.json"
    evaluation, delivery = load(evaluation_path), load(delivery_path)
    slurm = load(FULL / "CODE15_FULL_SLURM_RECEIPT.json")
    lineage = load(RESULTS / "EXPERIMENT_AND_CHECKPOINT_LINEAGE.json")["code15_full"]
    assert sha256(evaluation_path) == slurm["evaluation_receipt_sha256"] == lineage["evaluation_receipt_sha256"]
    assert sha256(delivery_path) == slurm["delivery_receipt_sha256"] == lineage["delivery_receipt_sha256"]
    for kind, source_hash in delivery["source_receipt_sha256"].items():
        receipt_field = "padding_audit_sha256" if kind == "padding" else f"{kind}_receipt_sha256"
        assert source_hash == slurm[receipt_field]
    assert {f"exams_part{i}.zip" for i in range(18)} == delivery["archives"].keys()
    assert {name: item["sha256"] for name, item in delivery["archives"].items()} == evaluation["archive_sha256"]
    assert delivery["crc_verified_archives"] == 18 and evaluation["complete_archive_coverage"]
    assert evaluation["reused_verified_first_archive"] and delivery["first_archive_bit_exact_rows_retained"] == 1411
    assert delivery["independent_metric_verification"]["status"] == "PASS"
    assert delivery["independent_metric_verification"]["metric_rows_verified"] == 20
    assert evaluation["point_estimates_independently_verified"]["patient_bootstrap_replayed"]
    assert delivery["duration_contract_10_seconds"] == "LIMITED"
    assert delivery["historical_patient_independence"] == "NOT_CERTIFIED"
    assert delivery["promotion_gates"] == {"P6": "FAIL", "P8": "FAIL"}
    assert delivery["p4"] == "NOT_EVALUABLE" and not lineage["promoted"]
    for job in ("33326", "33572", "33573", "33574", "33575"):
        assert slurm["jobs"][job]["state"] == "COMPLETED" and slurm["jobs"][job]["exit_code"] == "0:0"
    flow = delivery["cohort_flow"]
    assert flow == evaluation["cohort_flow"]
    assert flow["selected_ecgs"] == 43187 == 18001 + 504 + flow["final_paired_ecgs"]
    assert flow["selected_patients"] == 29081 == 11781 + flow["patients_with_scored_ecgs"]
    assert sum(sum(row["scored"].values()) for row in delivery["duration_distribution"].values()) == 24682
    assert sum(row["scored"]["581/581"] for row in delivery["duration_distribution"].values()) == 24578
    assert sha256(FULL / "CODE15_PER_CLASS.csv") == evaluation["aggregate_csv_sha256"]
    for filename, expected in evaluation["aggregate_views_sha256"].items():
        assert sha256(FULL / filename) == expected
    with (FULL / "EXTERNAL_CODE15_RESULTS.csv").open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        assert {"exam_id", "patient_id", "record_id", "statement"}.isdisjoint(reader.fieldnames)
        rows = list(reader)
    assert len(rows) == 20 and len({(row["profile"], row["endpoint"], row["model"]) for row in rows}) == 20
    for row in rows:
        assert row["scope"] == "FULL_FROZEN_SAMPLE" and row["estimable"] == "True"
        assert sum(int(row[key]) for key in ("tp", "tn", "fp", "fn")) == 24682


def test_development_replay_receipt_has_no_external_promotion():
    fit_path = RESULTS / "DEVELOPMENT_ABLATION_33296_1.json"
    replay_path = RESULTS / "DEVELOPMENT_ABLATION_REPLAY_33296_6.json"
    lineage = load(RESULTS / "EXPERIMENT_AND_CHECKPOINT_LINEAGE.json")["development_mlp"]
    assert lineage["fit_receipt_sha256"] == sha256(fit_path)
    assert lineage["replay_receipt_sha256"] == sha256(replay_path)
    fit, replay = load(fit_path), load(replay_path)
    assert not fit["code15_inputs_opened"] and not fit["mimic_inputs_opened"]
    assert replay["input_aggregate_sha256"] == fit["aggregate_csv_sha256"] == sha256(
        RESULTS / "SPECIALIST_IMPROVEMENT_EXPERIMENTS.csv"
    )
    assert replay["verified_original_rows"] == 60
    assert replay["bootstrap_unit"] == "ecg_record_not_patient"
    for contrasts in replay["contrasts_mlp_minus_linear"].values():
        for contrast in contrasts.values():
            assert contrast["delta_ci95"][0] <= 0
            assert not contrast["observed_metric_gate_pass"]


def test_boundary_and_limb_checks_are_distinct_from_clinical_eligibility(monkeypatch):
    pytest.importorskip("h5py")
    import numpy as np

    monkeypatch.syspath_prepend(str(ROOT / "scripts/external_validation"))
    from audit_code15_padding import border_counts, limb_consistency, limb_order_diagnostic

    lead_i = np.arange(2934, dtype=float) + 1
    lead_ii = 3 * lead_i + np.cos(lead_i)
    lead_iii = lead_ii - lead_i
    trace = np.column_stack((lead_i, lead_ii, lead_iii, -(lead_i + lead_ii) / 2,
                             (lead_i - lead_iii) / 2, (lead_ii + lead_iii) / 2,
                             *([lead_ii] * 6)))
    trace = np.pad(trace, ((581, 581), (0, 0)))
    assert border_counts(trace) == ("finite_nonzero", 581, 581)
    assert limb_consistency(trace).tolist() == [True, True, True, True]
    assert limb_order_diagnostic(trace)[2].tolist() == [0, 1, 2, 3]
    trace[:, 3] *= -1
    assert limb_consistency(trace).tolist() == [True, False, True, True]
    assert limb_order_diagnostic(trace)[2].tolist() == [0, 5, 2, 3]


def test_mimic_complete_inference_does_not_claim_performance():
    receipt_path = RESULTS / "MIMIC_LABEL_BLIND_INFERENCE_33296.json"
    receipt = load(receipt_path)
    audit = load(RESULTS / "PATIENT_SPLIT_AND_OVERLAP_AUDIT.json")["mimic"]
    jobs = load(RESULTS / "PR6_EXECUTION_SLURM_RECEIPT.json")
    assert audit["inference_receipt_sha256"] == sha256(receipt_path)
    assert receipt["waveform_qc_receipt_sha256"] == sha256(RESULTS / "MIMIC_QC_33295.json")
    assert receipt["eligible_ecgs"] == receipt["scored_ecgs"] == sum(audit["waveform_eligible_by_split"].values())
    assert jobs["jobs"]["33296"]["state"] == "COMPLETED" and jobs["jobs"]["33296"]["errors"] == 0
    assert receipt["failed_scoring"] == 0 and not receipt["performance_computed"] and not receipt["reference_read"]
    for route in receipt["threshold_routing"].values():
        assert route["threshold_set_empty"] + route["threshold_set_nonempty"] == receipt["scored_ecgs"]
        assert route["clinical_quarantine"] == "NOT_ASSESSED"
