from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_af_reference_code_agreement_is_not_longitudinal_validation():
    audit = load("outputs/results/revision_20261029/af_reference_consistency.json")
    for profile, records in (("primary6", 1643), ("primary8", 2193)):
        result = audit["profiles"][profile]
        assert result["records"] == records
        assert result["af_reference_positive"] == result["af_code_positive"] == 390
        assert result["af_flag_mismatches"] == 0
        assert result["unresolved_code_rows"] == 0


def test_sph_pvc_reference_is_record_statement_not_beat_detection():
    protocol = load("configs/external_validation/sph_frozen.json")
    endpoints = [item for item in protocol["endpoints"] if item["name"] == "PVC"]
    assert {item["profile"] for item in endpoints} == {"P6", "P8"}
    assert all(item["codes"] == [60] and "not beat detection" in item["reference"]
               for item in endpoints)
    results = load("outputs/results/external_sph/sph_aggregate_32669.json")
    for profile in ("P6", "P8"):
        endpoint = results["endpoints"][f"{profile}:PVC"]
        assert endpoint["scored_positive"] == 1067
        assert endpoint["scored_negative"] == 24703
