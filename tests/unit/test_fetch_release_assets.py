import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "fetch_release_assets", ROOT / "scripts/artifacts/fetch_release_assets.py"
)
fetch_release_assets = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fetch_release_assets)


def test_asset_selection_can_exclude_release_datasets():
    assets = [
        {"name": "backbone.pt", "category": "model"},
        {"name": "evaluation.tar.zst", "category": "external_dev_dataset"},
    ]

    selected = fetch_release_assets.select_assets(assets, ["backbone.pt"])

    assert selected == [assets[0]]


def test_asset_selection_rejects_unknown_names_and_duplicate_manifest_names():
    with pytest.raises(ValueError, match="unknown release asset"):
        fetch_release_assets.select_assets([{"name": "known.pt"}], ["missing.pt"])
    with pytest.raises(ValueError, match="duplicate asset names"):
        fetch_release_assets.select_assets([{"name": "same.pt"}, {"name": "same.pt"}], None)
