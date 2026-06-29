from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from titan_v45.artifacts.manifest import sha256_file


@dataclass(frozen=True)
class ReleaseAsset:
    source: str | Path
    name: str
    path: str
    category: str


def _download_url(repository: str, tag: str, asset_name: str) -> str:
    return f"https://github.com/{repository}/releases/download/{tag}/{asset_name}"


def build_release_manifest(
    *,
    assets: list[ReleaseAsset],
    repository: str,
    tag: str,
    manifest_path: str | Path,
    sha256sums_path: str | Path,
) -> dict[str, object]:
    manifest = Path(manifest_path)
    sha256sums = Path(sha256sums_path)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    sha256sums.parent.mkdir(parents=True, exist_ok=True)
    asset_rows: list[dict[str, object]] = []
    artifact_hashes: dict[str, str] = {}
    for asset in assets:
        source = Path(asset.source).resolve()
        if not source.is_file():
            raise FileNotFoundError(f"release asset is missing: {source}")
        digest = sha256_file(source)
        row = {
            "name": asset.name,
            "path": asset.path,
            "category": asset.category,
            "bytes": source.stat().st_size,
            "sha256": digest,
            "download_url": _download_url(repository, tag, asset.name),
        }
        asset_rows.append(row)
        artifact_hashes[asset.path] = digest
    payload: dict[str, object] = {
        "schema": "TITAN_V45_RELEASE_MANIFEST_V1",
        "repository": repository,
        "tag": tag,
        "assets": asset_rows,
        "artifacts": artifact_hashes,
    }
    manifest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    sums = [f"{row['sha256']}  {row['name']}" for row in asset_rows]
    sums.append(f"{sha256_file(manifest)}  {manifest.name}")
    sha256sums.write_text("\n".join(sums) + "\n", encoding="utf-8")
    return payload
