import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

from titan_v45.data.external_ecg import (
    LEADS,
    physical_digest,
    physical_mv,
    prepare_external,
    unpad_code,
)
from titan_v45.data.external_reference import REPORT_COLUMNS, classify_report
from titan_v45.evaluation.external_metrics import from_confusion


def test_select_is_order_independent_and_keeps_patients_together():
    script = Path(__file__).resolve().parents[2] / "scripts/external_validation/acquire_mimic.py"
    spec = importlib.util.spec_from_file_location("acquire_mimic", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rows = []
    for i in range(200):
        patient, study = str(10000000 + i // 2), str(40000000 + i)
        rows.append({"subject_id": patient, "study_id": study,
                     "path": f"files/p{patient[:4]}/p{patient}/s{study}/{study}"})
    kwargs = dict(seed="example", patient_limit=20, max_records=2)
    selected = list(module.select(rows, **kwargs))
    assert selected == list(module.select(reversed(rows), **kwargs))
    assert len(selected) == 40
    patients = {s: {r["subject_id"] for r in selected if r["split"] == s} for s in module.SPLITS}
    assert [len(x) for x in patients.values()] == [13, 2, 2, 3]
    assert len(set.union(*patients.values())) == 20
    with pytest.raises(ValueError, match="unexpected MIMIC path"):
        list(module.select([{**rows[0], "path": "../unexpected"}], **kwargs))


def test_reference_never_treats_absence_or_uncertainty_as_negative():
    report = dict.fromkeys(REPORT_COLUMNS, "")
    report.update(report_4="Atrial fibrillation", report_17="No premature atrial complexes",
                  report_3="Possible inferior infarct", report_2="Old anteroseptal infarct")
    labels = classify_report(report)
    assert labels["AFIB"] == "positive"
    assert labels["PAC"] == "explicit_negative"
    assert labels["IMI"] == "uncertain"
    assert labels["ASMI"] == "historical"
    assert labels["LVH"] == "unmentioned"
    assert labels["ISC_"] == "unmapped"
    report["report_5"] = "No evidence of atrial fibrillation"
    assert classify_report(report)["AFIB"] == "conflict"


def test_physical_conversion_and_canonical_order_are_explicit():
    signal = np.arange(5000, dtype=np.float32)[:, None] * np.arange(1, 13, dtype=np.float32)
    canonical = physical_mv(signal, LEADS, ["mV"] * 12, 500)
    reordered = physical_mv(1000 * signal[:, ::-1], LEADS[::-1], ["uV"] * 12, 500)
    assert physical_digest(canonical, 500) == physical_digest(reordered, 500)
    values, mask, morphology = prepare_external(canonical, 500, lambda x, fs: (x.shape, fs))
    assert values.shape == (12, 1250)
    assert mask.all()
    assert morphology == ((12, 1250), 125)
    with pytest.raises(ValueError, match="unknown_physical_unit"):
        physical_mv(signal, LEADS, ["ADC"] * 12, 500)


def test_code_padding_does_not_turn_seven_seconds_into_ten():
    short = np.pad(np.ones((2800, 12)), ((648, 648), (0, 0)))
    long = np.pad(np.ones((4000, 12)), ((48, 48), (0, 0)))
    assert unpad_code(long).shape == (4000, 12)
    with pytest.raises(ValueError, match="short_or_ambiguous_code_duration"):
        unpad_code(short)


def test_aggregate_metrics_do_not_impute_unsupported_f1():
    assert from_confusion(4, 1, 2, 3)["balanced_accuracy"] == pytest.approx((4 / 7 + 2 / 3) / 2)
    assert from_confusion(0, 1, 9, 0)["f1"] is None
    assert from_confusion(0, 0, 0, 0)["accuracy"] is None
    with pytest.raises(ValueError, match="nonnegative"):
        from_confusion(-1, 0, 0, 0)


def test_public_preflight_receipt_separates_selected_and_evaluable():
    root = Path(__file__).resolve().parents[2]
    result = root / "outputs/results/external_validation_20261111/EXTERNAL_VALIDATION_REPRODUCIBILITY.json"
    receipt = json.loads(result.read_text(encoding="utf-8"))
    docs = root / "docs/external_validation_20261111"
    for name, expected in (
        ("FROZEN_EXTERNAL_EVALUATION_PROTOCOL.json", receipt["protocol_sha256"]),
        ("REFERENCE_AUDIT_GATE.json", receipt["development_reference_support"]["gate_sha256"]),
    ):
        assert hashlib.sha256((docs / name).read_bytes()).hexdigest() == expected
    selected = receipt["frozen_mimic_selection"]
    assert sum(selected["ecgs_by_split"].values()) == selected["ecgs"] == 6784
    assert sum(selected["patients_by_split"].values()) == selected["patients"] == 4096
    assert selected["counts_are_selected_not_waveform_qc_eligible"]
    assert receipt["development_reference_support"]["endpoints_passed"] == 0
    assert not receipt["development_reference_support"]["retained_labels_extracted"]
    assert not receipt["frozen_model_probe"]["performance_computed"]
