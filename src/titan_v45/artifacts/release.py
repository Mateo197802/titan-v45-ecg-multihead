from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from titan_v45.artifacts.manifest import sha256_file


@dataclass(frozen=True)
class ReleaseAsset:
    source: str | Path
    name: str
    path: str
    category: str
    license: str | None = None
    source_lineage: str | None = None
    rights_review: str | None = None


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
        license_name = (asset.license or "").strip()
        source_lineage = (asset.source_lineage or "").strip()
        if not license_name or not source_lineage:
            raise ValueError(f"release asset requires license and source lineage: {asset.name}")
        if asset.category == "external_dev_dataset":
            if asset.rights_review != "cleared":
                raise ValueError(f"dataset asset requires rights_review=cleared: {asset.name}")
            metadata = f"{license_name} {source_lineage}".casefold()
            unresolved_markers = ("unresolved", "unverified", "unknown", "tbd", "hold")
            if any(re.search(rf"\b{marker}\b", metadata) for marker in unresolved_markers):
                raise ValueError(f"dataset asset has unresolved provenance or rights: {asset.name}")
        source = Path(asset.source).resolve()
        if not source.is_file():
            raise FileNotFoundError(f"release asset is missing: {source}")
        digest = sha256_file(source)
        row = {
            "name": asset.name,
            "path": asset.path,
            "category": asset.category,
            "license": license_name,
            "source_lineage": source_lineage,
            "rights_review": asset.rights_review,
            "bytes": source.stat().st_size,
            "sha256": digest,
            "download_url": _download_url(repository, tag, asset.name),
        }
        asset_rows.append(row)
        artifact_hashes[asset.path] = digest
    payload: dict[str, object] = {
        "schema": "TITAN_V45_RELEASE_MANIFEST_V2",
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
