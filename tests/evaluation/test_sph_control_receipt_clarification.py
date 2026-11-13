import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_receipt_field_is_metadata_digest_not_inventory_report_digest():
    outputs = ROOT / "outputs/results/external_sph"
    audit = json.loads((outputs / "sph_duplicate_amplitude_audit_32627.json").read_text())
    config = json.loads((ROOT / "configs/external_validation/sph_frozen.json").read_text())
    inventory = (outputs / "source_inventory_32617.json").read_bytes()
    actual_inventory = hashlib.sha256(inventory).hexdigest()
    assert audit["source_inventory_sha256"] == config["source_sha256"]["metadata.csv"]
    assert audit["source_inventory_sha256"] != actual_inventory
    assert actual_inventory == config["preperformance_controls"]["aggregates"]["source_inventory"]["sha256"]
    clarification = (ROOT / "docs/external_validation/sph_control_receipt_correction.md").read_text()
    assert actual_inventory in clarification
    assert audit["source_inventory_sha256"] in clarification
