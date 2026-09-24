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
                license="MODEL_LICENSE.md",
                source_lineage="outputs/models/release_weight_manifest.json",
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
    assert asset["license"] == "MODEL_LICENSE.md"
    assert asset["source_lineage"] == "outputs/models/release_weight_manifest.json"
    assert payload["schema"] == "TITAN_V45_RELEASE_MANIFEST_V2"
    assert asset["download_url"].endswith("/v0.1.0/backbone-v3f-original.pt")
    assert payload["artifacts"][asset["path"]] == asset["sha256"]
    sums = sha256sums.read_text(encoding="utf-8")
    assert "backbone-v3f-original.pt" in sums
    assert "release-manifest.json" in sums


def test_release_manifest_rejects_dataset_assets_with_unresolved_rights(tmp_path: Path) -> None:
    source = tmp_path / "cohort.tar.zst"
    source.write_bytes(b"cohort")

    try:
        build_release_manifest(
            assets=[
                ReleaseAsset(
                    source=source,
                    name="cohort.tar.zst",
                    path="data/external_dev/cohort.tar.zst",
                    category="external_dev_dataset",
                    license="CC-BY-4.0 with unresolved source",
                    source_lineage="source attribution pending",
                    rights_review="cleared",
                )
            ],
            repository="example/repo",
            tag="v0.2.0",
            manifest_path=tmp_path / "release-manifest.json",
            sha256sums_path=tmp_path / "SHA256SUMS",
        )
    except ValueError as error:
        assert "unresolved provenance or rights" in str(error)
    else:
        raise AssertionError("unresolved dataset rights must block release manifest generation")


def test_release_manifest_requires_explicit_dataset_rights_review(tmp_path: Path) -> None:
    source = tmp_path / "cohort.tar.zst"
    source.write_bytes(b"cohort")

    try:
        build_release_manifest(
            assets=[
                ReleaseAsset(
                    source=source,
                    name="cohort.tar.zst",
                    path="data/external_dev/cohort.tar.zst",
                    category="external_dev_dataset",
                    license="CC-BY-4.0",
                    source_lineage="verified upstream cohort",
                )
            ],
            repository="example/repo",
            tag="v0.2.0",
            manifest_path=tmp_path / "release-manifest.json",
            sha256sums_path=tmp_path / "SHA256SUMS",
        )
    except ValueError as error:
        assert "requires rights_review=cleared" in str(error)
    else:
        raise AssertionError("dataset assets must explicitly pass rights review")


def test_release_manifest_requires_license_and_lineage_for_every_asset(tmp_path: Path) -> None:
    source = tmp_path / "model.pt"
    source.write_bytes(b"model")

    try:
        build_release_manifest(
            assets=[
                ReleaseAsset(
                    source=source,
                    name="model.pt",
                    path="outputs/model.pt",
                    category="model",
                )
            ],
            repository="example/repo",
            tag="v0.2.0",
            manifest_path=tmp_path / "release-manifest.json",
            sha256sums_path=tmp_path / "SHA256SUMS",
        )
    except ValueError as error:
        assert "requires license and source lineage" in str(error)
    else:
        raise AssertionError("release manifest generation must require provenance metadata")
