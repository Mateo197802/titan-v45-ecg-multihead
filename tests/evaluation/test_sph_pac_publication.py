import csv
import hashlib
import json
from pathlib import Path

import pytest

from scripts.external_validation import prepare_sph_pac_publication as publication


def _write_source(directory, aha_codes):
    directory.mkdir()
    with (directory / "code.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("Category", "Code", "Description"))
        writer.writerow(("D", 12, "Other statement"))
        writer.writerow(("D", 30, "Atrial premature complex(es)"))
        writer.writerow(("D", 31, "Atrial premature complexes, nonconducted"))
        writer.writerow(("Modifier", 1, "Example modifier"))
    with (directory / "metadata.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("ECG_ID", "AHA_Code", "Patient_ID", "Age", "Sex", "N", "Date"))
        for index, code in enumerate(aha_codes, start=1):
            writer.writerow((f"A{index:05}", code, f"P{index}", 50, "F", 5000, "2020-01-01"))


def test_summarizes_code_30_and_31_without_exporting_source_ids(tmp_path, monkeypatch):
    source = tmp_path / "source"
    _write_source(source, ["30", "31", "30;31", "12"])
    expected = {
        "records": 4,
        "code_30_records": 2,
        "code_31_records": 2,
        "records_with_both_codes": 1,
        "code_31_only_records": 1,
        "code_30_only_records": 1,
        "neither_code_records": 1,
        "code_30_description": "Atrial premature complex(es)",
        "code_31_description": "Atrial premature complexes, nonconducted",
    }
    monkeypatch.setattr(publication, "EXPECTED_LABEL_CODE_AUDIT", expected)
    monkeypatch.setattr(publication, "EXPECTED_SOURCE_RECORDS", 4)

    audit = publication.summarize_label_policy(source)

    assert audit["records"] == 4
    assert audit["code_30_records"] == 2
    assert audit["code_31_records"] == 2
    assert audit["records_with_both_codes"] == 1
    assert audit["code_31_only_records"] == 1
    assert audit["code_30_only_records"] == 1
    assert audit["neither_code_records"] == 1
    assert "A00001" not in json.dumps(audit)
    assert "P1" not in json.dumps(audit)


def test_creates_scoped_publication_receipt_and_explicit_code_policy(monkeypatch):
    raw_aggregate = {
        "schema": "TITAN_V45_SPH_PAC_PROBE_AGGREGATE_V1",
        "target": "SPH primary code 30; code 31 excluded; ECG statement, not clinical adjudication",
    }
    raw_receipt = {
        "schema": "TITAN_V45_SPH_PAC_PROBE_RECEIPT_V1",
        "protocol_commit": "a" * 40,
        "protocol_config_sha256": "b" * 64,
        "public_aggregate_sha256": "c" * 64,
        "source_sha256": {"metadata.csv": "d" * 64},
        "v3f_checkpoint_sha256": "e" * 64,
        "embedding_archive_sha256": "f" * 64,
        "embedding_receipt_sha256": "1" * 64,
        "dependency_archive_sha256": {"python_deps": "2" * 64},
        "runtime": {"python": "3.11.14"},
        "private_model_bundle_sha256": "3" * 64,
        "labels_used_for_head_fitting": True,
        "threshold_or_model_tuning_on_holdout": False,
        "mimic_data_consulted": False,
        "row_level_data_in_repository": False,
        "slurm_job_id": "32884",
    }
    monkeypatch.setattr(publication, "EXPECTED_PROTOCOL_COMMIT", "a" * 40)
    monkeypatch.setattr(publication, "EXPECTED_PROTOCOL_CONFIG_SHA256", "b" * 64)
    monkeypatch.setattr(publication, "EXPECTED_EXECUTION_AGGREGATE_SHA256", "c" * 64)
    monkeypatch.setattr(publication, "EXPECTED_EXECUTION_RECEIPT_SHA256", "4" * 64)
    label_audit = publication.EXPECTED_LABEL_CODE_AUDIT

    aggregate, receipt = publication.normalize_execution_artifacts(
        raw_aggregate,
        raw_receipt,
        label_audit,
        execution_aggregate_sha256="c" * 64,
        execution_receipt_sha256="4" * 64,
    )

    assert aggregate["schema"] == "TITAN_V45_SPH_PAC_PROBE_AGGREGATE_V2"
    assert aggregate["label_code_audit"] == label_audit
    assert "code 31-only records remain included" in aggregate["target"]
    assert "not clinical negatives" in aggregate["target"]
    assert receipt["schema"] == "TITAN_V45_SPH_PAC_PUBLICATION_RECEIPT_V1"
    assert receipt["status"] == "exploratory_nonclinical_nonindependent"
    assert receipt["artifact_scope"] == "PAC probe public artifacts only"
    assert receipt["pac_row_level_data_in_public_artifacts"] is False
    assert "row_level_data_in_repository" not in receipt
    assert receipt["source_execution_receipt_sha256"] == "4" * 64
    assert receipt["publication_normalizer_sha256"] == hashlib.sha256(
        Path(publication.__file__).read_bytes()
    ).hexdigest()
    assert receipt["metric_validation"]["score_metrics_recomputed_from_row_scores"] is False
    assert receipt["metric_validation"]["confusion_derived_metrics_recomputed"] is True


def test_rejects_publication_from_unrecognized_execution_receipt_digest(monkeypatch):
    monkeypatch.setattr(publication, "EXPECTED_PROTOCOL_COMMIT", "a" * 40)
    monkeypatch.setattr(publication, "EXPECTED_PROTOCOL_CONFIG_SHA256", "b" * 64)
    monkeypatch.setattr(publication, "EXPECTED_EXECUTION_AGGREGATE_SHA256", "c" * 64)
    monkeypatch.setattr(publication, "EXPECTED_EXECUTION_RECEIPT_SHA256", "4" * 64)
    monkeypatch.setattr(publication, "EXPECTED_LABEL_CODE_AUDIT", {"audit": "stub"})

    with pytest.raises(ValueError, match="execution receipt SHA-256"):
        publication.normalize_execution_artifacts(
            {"schema": "TITAN_V45_SPH_PAC_PROBE_AGGREGATE_V1"},
            {"schema": "TITAN_V45_SPH_PAC_PROBE_RECEIPT_V1"},
            {},
            execution_aggregate_sha256="c" * 64,
            execution_receipt_sha256="5" * 64,
        )


def test_rejects_publication_from_unrecognized_frozen_protocol_commit(monkeypatch):
    monkeypatch.setattr(publication, "EXPECTED_PROTOCOL_COMMIT", "a" * 40)
    monkeypatch.setattr(publication, "EXPECTED_PROTOCOL_CONFIG_SHA256", "b" * 64)
    monkeypatch.setattr(publication, "EXPECTED_EXECUTION_AGGREGATE_SHA256", "c" * 64)
    monkeypatch.setattr(publication, "EXPECTED_EXECUTION_RECEIPT_SHA256", "4" * 64)
    monkeypatch.setattr(publication, "EXPECTED_LABEL_CODE_AUDIT", {"audit": "stub"})
    raw_receipt = {
        "schema": "TITAN_V45_SPH_PAC_PROBE_RECEIPT_V1",
        "protocol_commit": "f" * 40,
        "protocol_config_sha256": "b" * 64,
        "public_aggregate_sha256": "c" * 64,
    }

    with pytest.raises(ValueError, match="frozen protocol commit"):
        publication.normalize_execution_artifacts(
            {"schema": "TITAN_V45_SPH_PAC_PROBE_AGGREGATE_V1"},
            raw_receipt,
            {},
            execution_aggregate_sha256="c" * 64,
            execution_receipt_sha256="4" * 64,
        )
