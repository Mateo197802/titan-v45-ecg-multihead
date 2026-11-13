import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "configs/external_validation/sph_frozen.json"


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def test_frozen_sph_protocol_hashes_and_contracts_are_self_consistent():
    protocol = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    assert protocol["stage"] == "full_population"
    assert protocol["frozen_before_performance"] is True
    assert protocol["expected_source_records"] == 25770
    assert protocol["source_population"]["patients"] == 24666
    assert len(protocol["endpoints"]) == 14
    assert len({(row["profile"], row["name"]) for row in protocol["endpoints"]}) == 14
    assert protocol["preperformance_controls"]["independence_screen"][
        "independence_certified"
    ] is False

    for profile, classes in protocol["classes"].items():
        assert list(protocol["thresholds"][profile]) == classes
    for relative_path, expected in protocol["implementation_sha256"].items():
        assert _sha256(ROOT / relative_path) == expected, relative_path
    for control in protocol["preperformance_controls"]["aggregates"].values():
        assert _sha256(ROOT / control["path"]) == control["sha256"]

    manifest = json.loads((ROOT / "release-manifest.json").read_text(encoding="utf-8"))
    asset_hashes = {asset["name"]: asset["sha256"] for asset in manifest["assets"]}
    assert protocol["model_sha256"] == {
        name: asset_hashes[name] for name in protocol["model_sha256"]
    }
    assert protocol["source_population"]["physical_units"].startswith("not provided")
    assert protocol["thresholds"]["P4"]["ASMI"] == 0.6699999999999999
    assert protocol["quarantine"]["rate"] is None
    assert protocol["inference"]["route_uses_reference_labels"] is False
    assert protocol["reporting"]["input"].startswith("aggregate endpoint report")
    assert protocol["reporting"]["outputs"] == [
        "sph_profile_coverage", "sph_endpoint_metrics", "sph_duplicate_sensitivity"
    ]
