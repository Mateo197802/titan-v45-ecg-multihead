import hashlib
import json
import shutil
from pathlib import Path

import pytest

from scripts.external_validation.plot_sph_pac_probe import (
    generate_report,
    validate_public_pac_artifacts,
)

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "outputs/results/external_sph_pac"
AGGREGATE = RESULTS / "pac_probe_aggregate.json"
RECEIPT = RESULTS / "pac_probe_receipt.json"
CONFIG = ROOT / "configs/external_validation/pac_v3f_embedding_probe.json"


def _copy_inputs(directory):
    aggregate = directory / "pac_probe_aggregate.json"
    receipt = directory / "pac_probe_receipt.json"
    shutil.copyfile(AGGREGATE, aggregate)
    shutil.copyfile(RECEIPT, receipt)
    return aggregate, receipt


def _write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_validates_measured_aggregate_against_frozen_receipt():
    checked = validate_public_pac_artifacts(AGGREGATE, RECEIPT, CONFIG)

    assert checked["aggregate"]["source"]["metadata_records"] == 25_770
    assert checked["aggregate"]["split"]["train_records"] == 20_627
    assert checked["aggregate"]["split"]["holdout_records"] == 5_143
    assert checked["receipt"]["slurm_job_id"] == "32884"
    assert checked["aggregate_sha256"] == checked["receipt"]["public_aggregate_sha256"]
    assert checked["aggregate"]["models"]["fixed_mlp_sensitivity"]["holdout"][
        "point_estimates"
    ]["confusion"] == {"fn": 35, "fp": 211, "tn": 4826, "tp": 71}
    assert all(
        interval["invalid_replicates"] == 0
        for model in checked["aggregate"]["models"].values()
        for scope in model.values()
        for interval in scope["patient_cluster_bootstrap"]["intervals"].values()
    )


def test_rejects_aggregate_whose_receipt_hash_does_not_match(tmp_path):
    aggregate, receipt = _copy_inputs(tmp_path)
    receipt_value = json.loads(receipt.read_text(encoding="utf-8"))
    receipt_value["public_aggregate_sha256"] = "0" * 64
    _write_json(receipt, receipt_value)

    with pytest.raises(ValueError, match="aggregate SHA-256"):
        validate_public_pac_artifacts(aggregate, receipt, CONFIG)


def test_rejects_inconsistent_population_even_when_receipt_is_resealed(tmp_path):
    aggregate, receipt = _copy_inputs(tmp_path)
    aggregate_value = json.loads(aggregate.read_text(encoding="utf-8"))
    aggregate_value["source"]["metadata_records"] -= 1
    _write_json(aggregate, aggregate_value)
    receipt_value = json.loads(receipt.read_text(encoding="utf-8"))
    receipt_value["public_aggregate_sha256"] = hashlib.sha256(aggregate.read_bytes()).hexdigest()
    _write_json(receipt, receipt_value)

    with pytest.raises(ValueError, match="source record counts"):
        validate_public_pac_artifacts(aggregate, receipt, CONFIG)


def test_rejects_public_json_with_row_level_identifier(tmp_path):
    aggregate, receipt = _copy_inputs(tmp_path)
    aggregate_value = json.loads(aggregate.read_text(encoding="utf-8"))
    aggregate_value["unexpected"] = {"patient_id": "private"}
    _write_json(aggregate, aggregate_value)
    receipt_value = json.loads(receipt.read_text(encoding="utf-8"))
    receipt_value["public_aggregate_sha256"] = hashlib.sha256(aggregate.read_bytes()).hexdigest()
    _write_json(receipt, receipt_value)

    with pytest.raises(ValueError, match="identifier field"):
        validate_public_pac_artifacts(aggregate, receipt, CONFIG)


def test_rejects_metrics_that_do_not_match_confusion_counts(tmp_path):
    aggregate, receipt = _copy_inputs(tmp_path)
    aggregate_value = json.loads(aggregate.read_text(encoding="utf-8"))
    points = aggregate_value["models"]["fixed_mlp_sensitivity"]["holdout"]["point_estimates"]
    points["sensitivity"] += 0.01
    _write_json(aggregate, aggregate_value)
    receipt_value = json.loads(receipt.read_text(encoding="utf-8"))
    receipt_value["public_aggregate_sha256"] = hashlib.sha256(aggregate.read_bytes()).hexdigest()
    _write_json(receipt, receipt_value)

    with pytest.raises(ValueError, match="sensitivity does not reconcile"):
        validate_public_pac_artifacts(aggregate, receipt, CONFIG)


def test_rejects_protocol_commit_substitution_even_with_a_valid_sha_shape(tmp_path):
    aggregate, receipt = _copy_inputs(tmp_path)
    receipt_value = json.loads(receipt.read_text(encoding="utf-8"))
    receipt_value["protocol_commit"] = "a" * 40
    _write_json(receipt, receipt_value)

    with pytest.raises(ValueError, match="frozen protocol commit"):
        validate_public_pac_artifacts(aggregate, receipt, CONFIG)


def test_rejects_publication_normalizer_substitution(tmp_path):
    aggregate, receipt = _copy_inputs(tmp_path)
    receipt_value = json.loads(receipt.read_text(encoding="utf-8"))
    receipt_value["publication_normalizer_sha256"] = "a" * 64
    _write_json(receipt, receipt_value)

    with pytest.raises(ValueError, match="normalizer SHA-256"):
        validate_public_pac_artifacts(aggregate, receipt, CONFIG)


def test_rejects_unrecognized_row_hash_fields_even_when_receipt_is_resealed(tmp_path):
    aggregate, receipt = _copy_inputs(tmp_path)
    aggregate_value = json.loads(aggregate.read_text(encoding="utf-8"))
    aggregate_value["duplicate_audit"]["record_sha256"] = "f" * 64
    _write_json(aggregate, aggregate_value)
    receipt_value = json.loads(receipt.read_text(encoding="utf-8"))
    receipt_value["public_aggregate_sha256"] = hashlib.sha256(aggregate.read_bytes()).hexdigest()
    _write_json(receipt, receipt_value)

    with pytest.raises(ValueError, match="row-level field"):
        validate_public_pac_artifacts(aggregate, receipt, CONFIG)


def test_rejects_row_prediction_arrays_even_when_receipt_is_resealed(tmp_path):
    aggregate, receipt = _copy_inputs(tmp_path)
    aggregate_value = json.loads(aggregate.read_text(encoding="utf-8"))
    aggregate_value["models"]["weighted_l2_logistic"]["holdout"]["row_predictions"] = [0, 1]
    _write_json(aggregate, aggregate_value)
    receipt_value = json.loads(receipt.read_text(encoding="utf-8"))
    receipt_value["public_aggregate_sha256"] = hashlib.sha256(aggregate.read_bytes()).hexdigest()
    _write_json(receipt, receipt_value)

    with pytest.raises(ValueError, match="row-level field"):
        validate_public_pac_artifacts(aggregate, receipt, CONFIG)


def test_rejects_fitted_weights_in_receipt_even_when_aggregate_is_unchanged(tmp_path):
    aggregate, receipt = _copy_inputs(tmp_path)
    receipt_value = json.loads(receipt.read_text(encoding="utf-8"))
    receipt_value["fitted_weights"] = [0.25, -0.25]
    _write_json(receipt, receipt_value)

    with pytest.raises(ValueError, match="row-level field"):
        validate_public_pac_artifacts(aggregate, receipt, CONFIG)


def test_rejects_score_metric_substitution_even_when_receipt_is_resealed(tmp_path):
    aggregate, receipt = _copy_inputs(tmp_path)
    aggregate_value = json.loads(aggregate.read_text(encoding="utf-8"))
    points = aggregate_value["models"]["weighted_l2_logistic"]["holdout"]["point_estimates"]
    points["auroc"] += 0.001
    _write_json(aggregate, aggregate_value)
    receipt_value = json.loads(receipt.read_text(encoding="utf-8"))
    receipt_value["public_aggregate_sha256"] = hashlib.sha256(aggregate.read_bytes()).hexdigest()
    _write_json(receipt, receipt_value)

    with pytest.raises(ValueError, match="published aggregate SHA-256"):
        validate_public_pac_artifacts(aggregate, receipt, CONFIG)


def test_generates_aggregate_only_figure_and_hash_manifest(tmp_path):
    pytest.importorskip("matplotlib")
    manifest = generate_report(AGGREGATE, RECEIPT, CONFIG, tmp_path)

    assert manifest["schema"] == "TITAN_V45_SPH_PAC_FIGURE_MANIFEST_V1"
    assert manifest["privacy"] == {
        "individual_identifiers_present": False,
        "row_level_predictions_present": False,
        "probe_weights_present": False,
        "mimic_data_consulted": False,
    }
    assert set(manifest["figures"]) == {
        "sph_pac_probe_exploratory.png",
        "sph_pac_probe_exploratory.pdf",
    }
    for name, item in manifest["figures"].items():
        path = tmp_path / name
        assert item["bytes"] == path.stat().st_size > 0
        assert item["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert (tmp_path / "pac_probe_figure_manifest.json").is_file()
