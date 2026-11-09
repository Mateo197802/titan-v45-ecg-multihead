from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest
import torch

from titan_v45.benchmarkmax.pac import pool_v3f_meanmax
from titan_v45.models.backbone import TitanV4Hybrid

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "run_sph_pac_head_comparison",
    ROOT / "scripts/benchmarkmax/run_sph_pac_head_comparison.py",
)
assert SPEC is not None and SPEC.loader is not None
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


def _small_backbone() -> TitanV4Hybrid:
    torch.manual_seed(17)
    return TitanV4Hybrid(
        morphology_dim=0,
        d_model=16,
        num_transformer_layers=1,
        nhead=4,
        stage_channels=(8, 16, 32, 64),
        dropout=0.0,
    ).eval()


def test_label_blind_index_does_not_parse_diagnostic_statements(tmp_path: Path) -> None:
    path = tmp_path / "metadata.csv"
    path.write_text(
        "ECG_ID,AHA_Code,Patient_ID,Age,Sex,N,Date\nA00001,not-a-code,p1,40,F,5000,2020\n",
        encoding="utf-8",
    )

    assert RUNNER.read_label_blind_signal_index(path) == {"A00001": 5000}


def test_frozen_p8_scores_require_matching_receipt_and_complete_scored_ledger(
    tmp_path: Path,
) -> None:
    ledger_path = tmp_path / "private-predictions.jsonl"
    rows = [
        {"record_id": "A00001", "status": "scored", "profiles": {"P8": {"scores": {"PAC": 0.2}}}},
        {"record_id": "A00002", "status": "scored", "profiles": {"P8": {"scores": {"PAC": 0.8}}}},
    ]
    ledger_path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    source_hashes = {"metadata.csv": "a" * 64, "code.csv": "b" * 64, "records.tar.gz": "c" * 64}
    model_hash = "d" * 64
    receipt = {
        "schema": "TITAN_V45_SPH_SCORING_RECEIPT_V1",
        "stage": "full_population",
        "job_id": "32668",
        "ledger_sha256": hashlib.sha256(ledger_path.read_bytes()).hexdigest(),
        "source_sha256": source_hashes,
        "model_sha256": {"specialists-v3q-primary8-best-candidate.pt": model_hash},
        "flow": {
            "metadata_records": 2,
            "archive_records": 2,
            "scored_records": 2,
            "status_counts": {"scored": 2},
        },
        "labels_used_for_inference_or_routing": False,
    }
    receipt_path = tmp_path / "scoring-receipt.json"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    scores = RUNNER.load_frozen_p8_pac_scores(
        ledger_path,
        receipt_path,
        expected_ledger_sha256=receipt["ledger_sha256"],
        expected_receipt_sha256=RUNNER.sha256_file(receipt_path),
        expected_job_id="32668",
        expected_source_sha256=source_hashes,
        expected_model_sha256=model_hash,
        expected_records=2,
    )

    assert scores == {"A00001": 0.2, "A00002": 0.8}


def test_frozen_p8_scores_reject_incomplete_or_label_aware_ledger(tmp_path: Path) -> None:
    ledger_path = tmp_path / "private-predictions.jsonl"
    ledger_path.write_text(
        json.dumps({"record_id": "A00001", "status": "scored", "profiles": {"P8": {"scores": {"PAC": 0.2}}}}) + "\n",
        encoding="utf-8",
    )
    source_hashes = {"metadata.csv": "a" * 64}
    model_hash = "d" * 64
    receipt = {
        "schema": "TITAN_V45_SPH_SCORING_RECEIPT_V1",
        "stage": "full_population",
        "job_id": "32668",
        "ledger_sha256": hashlib.sha256(ledger_path.read_bytes()).hexdigest(),
        "source_sha256": source_hashes,
        "model_sha256": {"specialists-v3q-primary8-best-candidate.pt": model_hash},
        "flow": {
            "metadata_records": 1,
            "archive_records": 1,
            "scored_records": 1,
            "status_counts": {"scored": 1},
        },
        "labels_used_for_inference_or_routing": True,
    }
    receipt_path = tmp_path / "scoring-receipt.json"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    with pytest.raises(ValueError, match="receipt|population"):
        RUNNER.load_frozen_p8_pac_scores(
            ledger_path,
            receipt_path,
            expected_ledger_sha256=receipt["ledger_sha256"],
            expected_receipt_sha256=RUNNER.sha256_file(receipt_path),
            expected_job_id="32668",
            expected_source_sha256=source_hashes,
            expected_model_sha256=model_hash,
            expected_records=2,
        )


def test_source_statement_support_reader_uses_source_level_contract() -> None:
    source = {
        "source_statement_counts_before_signal_exclusions": {
            "code_30_records": 1,
            "code_31_records": 1,
            "counts_verified_against_source_inventory": True,
        }
    }
    labels = {
        "A00001": ("P00001", True, False),
        "A00002": ("P00002", False, True),
    }

    assert RUNNER.validate_source_statement_counts(labels, source) == {
        "code_30_records": 1,
        "code_31_records": 1,
    }


def test_source_statement_support_reader_rejects_inventory_mismatch() -> None:
    source = {
        "source_statement_counts_before_signal_exclusions": {
            "code_30_records": 0,
            "code_31_records": 1,
            "counts_verified_against_source_inventory": True,
        }
    }
    labels = {"A00001": ("P00001", True, False)}

    with pytest.raises(ValueError, match="source PAC statement supports"):
        RUNNER.validate_source_statement_counts(labels, source)


def test_pac_config_freezes_all_declared_mlp_seeds_and_v45_baseline() -> None:
    config = json.loads((ROOT / "configs/benchmarkmax/sph_pac_head_comparison.json").read_text())

    assert config["training"]["mlp"]["seeds"] == [197802, 197803, 197804, 197805, 197806]
    assert config["training"]["mlp"]["hidden_dim"] == 192
    assert config["training"]["mlp"]["dropout"] == 0.25
    assert config["p8_baseline"]["threshold"] == 0.45
    assert config["p8_baseline"]["job_id"] == "32668"
    source_labels = {
        f"A{index:05d}": (
            f"P{index:05d}", index < 539, 539 <= index < 543,
        )
        for index in range(543)
    }
    assert RUNNER.validate_source_statement_counts(source_labels, config["source"]) == {
        "code_30_records": 539,
        "code_31_records": 4,
    }


def test_pac_config_preflight_rejects_incomplete_metric_contract() -> None:
    config = json.loads((ROOT / "configs/benchmarkmax/sph_pac_head_comparison.json").read_text())
    config["metrics"].pop("ece_bins")

    with pytest.raises(ValueError, match="ece_bins"):
        RUNNER.validate_frozen_pac_config(config)


def test_pac_config_metric_contract_matches_frozen_protocol() -> None:
    config = json.loads((ROOT / "configs/benchmarkmax/sph_pac_head_comparison.json").read_text())

    RUNNER.validate_frozen_pac_config(config)

    assert config["metrics"]["ece_bins"] == 10
    assert config["metrics"]["confidence_intervals"]["replicates"] == 2000
    assert config["metrics"]["confidence_intervals"]["seed"] == 197813


def test_pac_config_preflight_rejects_missing_mlp_patience_setting() -> None:
    config = json.loads((ROOT / "configs/benchmarkmax/sph_pac_head_comparison.json").read_text())
    config["training"]["mlp"].pop("patience_epochs")

    with pytest.raises(ValueError, match="training.mlp.patience_epochs"):
        RUNNER.validate_frozen_pac_config(config)


def test_streaming_meanmax_pool_matches_whole_record_pool_across_microbatches() -> None:
    model = _small_backbone()
    signals = torch.randn(3, 12, 1250)
    masks = torch.ones(3, 12, dtype=torch.bool)
    windows = [(signals[index].numpy(), masks[index].numpy(), np.zeros(10)) for index in range(3)]

    actual = RUNNER.embed_record_batch(
        model,
        [("A00001", windows[:2]), ("A00002", windows[2:])],
        torch.device("cpu"),
        windows_per_batch=1,
    )
    expected_first = pool_v3f_meanmax(model, signals[:2], masks[:2]).squeeze(0)
    expected_second = pool_v3f_meanmax(model, signals[2:], masks[2:]).squeeze(0)

    np.testing.assert_allclose(actual["A00001"], expected_first.detach().numpy(), rtol=0, atol=1e-6)
    np.testing.assert_allclose(actual["A00002"], expected_second.detach().numpy(), rtol=0, atol=1e-6)
