import hashlib
import json

import pytest

from titan_v45.evaluation.sph_report import evaluate_sph_ledger


def test_sph_endpoint_report_checks_sealed_ledger_and_patient_cluster_ci(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "code.csv").write_text(
        "Category,Code,Description\nPrimary,50,Atrial fibrillation\nPrimary,51,Other statement\n"
        "Modifier,346,Example modifier\n",
        encoding="utf-8",
    )
    (source / "metadata.csv").write_text(
        "ECG_ID,AHA_Code,Patient_ID,Age,Sex,N,Date\n"
        "A00001,50,P1,50,F,5000,2020-01-01\n"
        "A00002,51,P1,50,F,5000,2020-01-01\n"
        "A00003,50,P2,50,F,5000,2020-01-01\n",
        encoding="utf-8",
    )
    ledger = tmp_path / "ledger.jsonl"
    rows = [
        {"record_id": "A00001", "status": "scored", "profiles": {
            "P6": {"scores": {"AFIB": 0.9}, "labels": ["AFIB"],
                   "top1": "AFIB", "used_fallback": False}}},
        {"record_id": "A00002", "status": "scored", "profiles": {
            "P6": {"scores": {"AFIB": 0.1}, "labels": [],
                   "top1": "SB", "used_fallback": False}}},
        {"record_id": "A00003", "status": "technical_exclusion", "reason": "ValueError"},
    ]
    ledger.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    duplicate_index = tmp_path / "duplicates.jsonl"
    duplicate_index.write_text(
        "".join(json.dumps(row) + "\n" for row in [
            {"ecg_id": "A00001", "patient_id": "P1", "signal_sha256_canonical_f64": "x"},
            {"ecg_id": "A00002", "patient_id": "P1", "signal_sha256_canonical_f64": "y"},
            {"ecg_id": "A00003", "patient_id": "P2", "signal_sha256_canonical_f64": "x"},
        ]),
        encoding="utf-8",
    )
    receipt = tmp_path / "receipt.json"
    duplicate_index_sha256 = hashlib.sha256(duplicate_index.read_bytes()).hexdigest()
    control_hashes = {"source_inventory": "c" * 64}
    implementation_hashes = {"script.py": "d" * 64}
    receipt.write_text(json.dumps({
        "ledger_sha256": hashlib.sha256(ledger.read_bytes()).hexdigest(),
        "stage": "full_population",
        "protocol_commit": "a" * 40,
        "protocol_sha256": "b" * 64,
        "source_sha256": {},
        "model_sha256": {},
        "preperformance_control_sha256": control_hashes,
        "private_duplicate_index_sha256": duplicate_index_sha256,
        "implementation_sha256": implementation_hashes,
        "flow": {"archive_records": 3},
    }), encoding="utf-8")
    protocol = {
        "expected_source_records": 3,
        "endpoints": [{"profile": "P6", "name": "AFIB", "codes": [50],
                       "reference": "defensible ECG statement"}],
        "metrics": {"ece_bins": 10},
        "bootstrap": {"seed": 197813, "replicates": 30},
        "preperformance_controls": {
            "aggregates": {"source_inventory": {"sha256": "c" * 64}},
            "private_duplicate_index_sha256": duplicate_index_sha256,
        },
        "implementation_sha256": implementation_hashes,
    }
    report = evaluate_sph_ledger(
        source=source, ledger=ledger, scoring_receipt=receipt,
        duplicate_index=duplicate_index, protocol=protocol,
    )
    endpoint = report["endpoints"]["P6:AFIB"]
    assert report["full_population_flow"]["source_metadata_records"] == 3
    assert report["full_population_flow"]["technical_exclusions"] == 1
    assert endpoint["source_statement_positive"] == 2
    assert endpoint["scored_evaluable_records"] == 2
    assert endpoint["metrics"]["tp"] == 1
    assert endpoint["metrics"]["tn"] == 1
    assert endpoint["cluster_bootstrap_ci95"]["_design"]["unit"].startswith("connected_component")
    assert endpoint["cluster_bootstrap_ci95"]["accuracy"]["valid_replicates"] > 0
    assert report["full_population_flow"]["quarantine_rate"] is None
    assert report["profile_flow"]["P6"]["scored_records"] == 2
    assert report["profile_flow"]["P6"]["coverage"] == 2 / 3
    assert report["profile_flow"]["P6"]["empty_label_set_records"] == 1


def test_sph_endpoint_report_rejects_unsealed_or_incomplete_ledger(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    ledger.write_text("", encoding="utf-8")
    receipt = tmp_path / "receipt.json"
    receipt.write_text(json.dumps({
        "ledger_sha256": "0" * 64, "stage": "full_population",
    }), encoding="utf-8")
    source = tmp_path / "source"
    source.mkdir()
    (source / "code.csv").write_text(
        "Category,Code,Description\nPrimary,50,AFIB\nModifier,346,M\n",
        encoding="utf-8",
    )
    (source / "metadata.csv").write_text(
        "ECG_ID,AHA_Code,Patient_ID,Age,Sex,N,Date\nA00001,50,P1,50,F,5000,2020-01-01\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="hash"):
        evaluate_sph_ledger(source=source, ledger=ledger, scoring_receipt=receipt,
                            duplicate_index=tmp_path / "missing.jsonl", protocol={})


def test_endpoint_sensitivity_excludes_only_discordant_exact_signal_groups(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "code.csv").write_text(
        "Category,Code,Description\nPrimary,50,Atrial fibrillation\n"
        "Primary,51,Other statement\nModifier,346,Example modifier\n",
        encoding="utf-8",
    )
    (source / "metadata.csv").write_text(
        "ECG_ID,AHA_Code,Patient_ID,Age,Sex,N,Date\n"
        "A00001,50,P1,50,F,5000,2020-01-01\n"
        "A00002,51,P2,50,F,5000,2020-01-01\n"
        "A00003,50,P3,50,F,5000,2020-01-01\n"
        "A00004,51,P4,50,F,5000,2020-01-01\n",
        encoding="utf-8",
    )
    profiles = [
        {"scores": {"AFIB": score}, "labels": ["AFIB"] if score >= 0.5 else [],
         "top1": "AFIB" if score >= 0.5 else "SB", "used_fallback": False}
        for score in (0.9, 0.1, 0.8, 0.2)
    ]
    ledger = tmp_path / "ledger.jsonl"
    ledger.write_text("".join(json.dumps({
        "record_id": f"A{i:05d}", "status": "scored", "profiles": {"P6": profile}
    }) + "\n" for i, profile in enumerate(profiles, start=1)), encoding="utf-8")
    duplicate_index = tmp_path / "duplicates.jsonl"
    duplicate_index.write_text("".join(json.dumps({
        "ecg_id": f"A{i:05d}", "patient_id": f"P{i}",
        "signal_sha256_canonical_f64": digest,
    }) + "\n" for i, digest in enumerate(("same", "same", "pos", "neg"), start=1)),
        encoding="utf-8",
    )
    receipt = tmp_path / "receipt.json"
    duplicate_index_sha256 = hashlib.sha256(duplicate_index.read_bytes()).hexdigest()
    control_hashes = {"source_inventory": "c" * 64}
    implementation_hashes = {"script.py": "d" * 64}
    receipt.write_text(json.dumps({
        "ledger_sha256": hashlib.sha256(ledger.read_bytes()).hexdigest(),
        "stage": "full_population", "protocol_commit": "a" * 40,
        "protocol_sha256": "b" * 64, "source_sha256": {}, "model_sha256": {},
        "preperformance_control_sha256": control_hashes,
        "private_duplicate_index_sha256": duplicate_index_sha256,
        "implementation_sha256": implementation_hashes,
        "flow": {"archive_records": 4},
    }), encoding="utf-8")
    protocol = {
        "expected_source_records": 4,
        "endpoints": [{"profile": "P6", "name": "AFIB", "codes": [50],
                       "reference": "documented ECG statement"}],
        "metrics": {"ece_bins": 10},
        "bootstrap": {"seed": 197813, "replicates": 30},
        "preperformance_controls": {
            "aggregates": {"source_inventory": {"sha256": "c" * 64}},
            "private_duplicate_index_sha256": duplicate_index_sha256,
        },
        "implementation_sha256": implementation_hashes,
    }

    report = evaluate_sph_ledger(
        source=source, ledger=ledger, scoring_receipt=receipt,
        duplicate_index=duplicate_index, protocol=protocol,
    )
    endpoint = report["endpoints"]["P6:AFIB"]
    sensitivity = endpoint["discordant_exact_duplicate_sensitivity"]
    assert endpoint["metrics"]["rows"] == 4
    assert sensitivity["conflicting_duplicate_groups"] == 1
    assert sensitivity["source_records_excluded"] == 2
    assert sensitivity["scored_records_retained"] == 2
    assert sensitivity["metrics"]["rows"] == 2
