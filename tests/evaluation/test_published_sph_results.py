import hashlib
import json
from pathlib import Path

from scripts.external_validation.normalize_sph_aggregate import normalize_report
from scripts.external_validation.validate_sph_aggregate import validate_report
from scripts.external_validation.validate_sph_receipts import validate_receipts

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/results/external_sph"


def test_published_sph_results_match_receipts_and_normalization():
    config = ROOT / "configs/external_validation/sph_frozen.json"
    score = OUT / "scoring_receipt_32668.json"
    raw = OUT / "sph_aggregate_32669.json"
    normalized = OUT / "sph_aggregate_normalized_32669.json"
    aggregation = OUT / "sph_aggregation_receipt_32669.json"
    correction = OUT / "sph_ece_correction_receipt_32669.json"
    wrapper = ROOT / "scripts/external_validation/evaluate_sph_ece_corrected.py"
    assert validate_receipts(config, score, raw, aggregation, correction, wrapper)["checks_passed"] == 19
    config_data = json.loads(config.read_text(encoding="utf-8"))
    raw_data = json.loads(raw.read_text(encoding="utf-8"))
    normalized_data = json.loads(normalized.read_text(encoding="utf-8"))
    assert normalized_data == normalize_report(raw_data, hashlib.sha256(raw.read_bytes()).hexdigest())
    assert validate_report(normalized_data, config_data)["endpoints_checked"] == 14
    independent = json.loads((OUT / "sph_independent_points_32672.json").read_text(encoding="utf-8"))
    assert independent["individual_records_exported"] is False
    assert independent["inputs"]["aggregate_sha256"] == hashlib.sha256(raw.read_bytes()).hexdigest()
    assert independent["inputs"]["ledger_sha256"] == json.loads(score.read_text(encoding="utf-8"))["ledger_sha256"]
    assert len(independent["endpoints"]) == 14
    assert all(row == {"records": 25770, "checks_passed": 8} for row in independent["endpoints"].values())
    bootstrap_path = OUT / "sph_independent_bootstrap_32677.json"
    bootstrap = json.loads(bootstrap_path.read_text(encoding="utf-8"))
    assert hashlib.sha256(bootstrap_path.read_bytes()).hexdigest() == (
        "1beb13bbabd38308efcdf929740e16e6b75dd018ddc6b916022789eb41cfb52f"
    )
    assert bootstrap["individual_records_exported"] is False
    assert bootstrap["inputs"]["aggregate"] == hashlib.sha256(raw.read_bytes()).hexdigest()
    assert bootstrap["inputs"]["ledger"] == independent["inputs"]["ledger_sha256"]
    assert set(bootstrap["endpoints"]) == set(independent["endpoints"])
    assert all(row == {"binary_metrics": 6, "primary_and_sensitivity": True}
               for row in bootstrap["endpoints"].values())
