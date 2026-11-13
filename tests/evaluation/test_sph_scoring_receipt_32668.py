import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_scoring_receipt_matches_frozen_contract_and_contains_no_record_ids():
    receipt_path = ROOT / "outputs/results/external_sph/scoring_receipt_32668.json"
    config_path = ROOT / "configs/external_validation/sph_frozen.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    config = json.loads(config_path.read_text(encoding="utf-8"))
    assert hashlib.sha256(receipt_path.read_bytes()).hexdigest() == (
        "8abdc5f6561fc3fea77eeb68e8aa34bc2d02396cad9c2e9fbeea70b4188dac92"
    )
    assert receipt["protocol_sha256"] == hashlib.sha256(config_path.read_bytes()).hexdigest()
    assert receipt["model_sha256"] == config["model_sha256"]
    assert receipt["source_sha256"] == config["source_sha256"]
    assert receipt["implementation_sha256"] == config["implementation_sha256"]
    assert receipt["flow"]["status_counts"] == {"scored": config["expected_source_records"]}
    assert receipt["flow"]["metadata_records"] == receipt["flow"]["archive_records"] == 25770
    assert receipt["labels_used_for_inference_or_routing"] is False
    assert not re.search(r'"A[0-9]{5}"', receipt_path.read_text(encoding="utf-8"))
