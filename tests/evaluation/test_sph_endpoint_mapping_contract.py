import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_frozen_endpoints_use_only_defensible_mappings_with_source_support():
    config = json.loads((ROOT / "configs/external_validation/sph_frozen.json").read_text(encoding="utf-8"))
    mapping = json.loads((ROOT / "docs/external_validation/sph_label_harmonization.json").read_text(encoding="utf-8"))
    inventory = json.loads((ROOT / "outputs/results/external_sph/source_inventory_32617.json").read_text(encoding="utf-8"))
    endpoints = config["endpoints"]
    assert len(endpoints) == mapping["primary_endpoint_count"] == 14
    assert len({(row["profile"], row["name"]) for row in endpoints}) == len(endpoints)
    for row in endpoints:
        assert row["name"] in config["classes"][row["profile"]]
        target = mapping["mappings"][row["name"]]
        assert target["status"] == "EXACT_OR_DEFENSIBLE"
        assert row["codes"] == target["codes"]
        assert all(inventory["primary_statement_counts"][str(code)] > 0 for code in row["codes"])
    assert {row["name"] for row in endpoints}.isdisjoint({"NSR", "1AVB", "ISC_"})
    assert config["reference_policy"]["not_evaluable"] == {"NSR": [1], "1AVB": [82], "ISC_": [145, 146]}
