from __future__ import annotations

import json
from pathlib import Path

from titan_v45.artifacts.release import ReleaseAsset, build_release_manifest


def test_build_release_manifest_records_hashes_urls_and_sha256sums(tmp_path: Path) -> None:
    source = tmp_path / "backbone-v3f-original.pt"
    source.write_bytes(b"checkpoint")
    manifest = tmp_path / "release-manifest.json"
    sha256sums = tmp_path / "SHA256SUMS"

    build_release_manifest(
        assets=[
            ReleaseAsset(
                source=source,
                name="backbone-v3f-original.pt",
                path="outputs/models/backbones/backbone-v3f-original.pt",
                category="model",
            )
        ],
        repository="Mateo197802/titan-v45-ecg-multihead",
        tag="v0.1.0",
        manifest_path=manifest,
        sha256sums_path=sha256sums,
    )

    payload = json.loads(manifest.read_text(encoding="utf-8"))
    asset = payload["assets"][0]
    assert asset["name"] == "backbone-v3f-original.pt"
    assert asset["path"] == "outputs/models/backbones/backbone-v3f-original.pt"
    assert asset["download_url"].endswith("/v0.1.0/backbone-v3f-original.pt")
    assert payload["artifacts"][asset["path"]] == asset["sha256"]
    sums = sha256sums.read_text(encoding="utf-8")
    assert "backbone-v3f-original.pt" in sums
    assert "release-manifest.json" in sums
