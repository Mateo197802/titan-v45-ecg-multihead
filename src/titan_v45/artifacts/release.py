from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from titan_v45.artifacts.manifest import sha256_file

# These are the rejected example values from the submitted manuscript's A10.
REJECTED_A10_HASHES = frozenset({
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "a1b2c3d4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef0",
    "9f8e7d6c5b4a3210fedcba9876543210abcdef0123456789abcdef0123456789",
    "123456789abcdef0123456789abcdef0a1b2c3d4e5f60718293a4b5c6d7e8f90",
    "fedcba9876543210abcdef01234567899f8e7d6c5b4a3210fedcba9876543210",
})


def validate_release_manifest_hashes(payload: Mapping[str, Any]) -> None:
    if not isinstance(payload, Mapping):
        raise ValueError("release manifest must be an object")
    assets = payload.get("assets")
    if not isinstance(assets, list) or not assets:
        raise ValueError("release manifest requires nonempty assets")
    names: set[str] = set()
    paths: set[str] = set()
    hashes: dict[str, str] = {}
    for asset in assets:
        if not isinstance(asset, dict):
            raise ValueError("release asset must be an object")
        name, path = asset.get("name"), asset.get("path")
        if not isinstance(name, str) or not name or "/" in name or "\\" in name:
            raise ValueError("release asset requires a file name")
        if not isinstance(path, str) or not path or "\\" in path:
            raise ValueError(f"invalid release asset path: {name}")
        if PurePosixPath(path).is_absolute() or ".." in PurePosixPath(path).parts:
            raise ValueError(f"release asset escapes root: {name}")
        if name in names or path in paths:
            raise ValueError(f"duplicate release asset: {name}")
        names.add(name)
        paths.add(path)
        size, digest = asset.get("bytes"), asset.get("sha256")
        if type(size) is not int or size <= 0:
            raise ValueError(f"nonpositive or invalid release asset bytes: {name}")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
            raise ValueError(f"invalid SHA-256: {name}")
        if digest.lower() in REJECTED_A10_HASHES or len(set(digest.lower())) == 1:
            raise ValueError(f"empty or placeholder SHA-256: {name}")
        hashes[path] = digest
    if payload.get("artifacts") != hashes:
        raise ValueError("release artifacts map disagrees with asset hashes")


def audit_release_hashes(root: str | Path, *, require_models: bool = False) -> dict[str, Any]:
    base = Path(root).resolve()
    manifest = base / "release-manifest.json"
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    validate_release_manifest_hashes(payload)
    verified, missing = [], []
    for asset in payload["assets"]:
        path = (base / asset["path"]).resolve()
        if not path.is_relative_to(base):
            raise ValueError(f"release asset escapes root: {asset['name']}")
        if not path.is_file():
            if require_models and asset.get("category") == "model":
                raise ValueError(f"required model is missing: {asset['name']}")
            missing.append(asset["name"])
            continue
        size, digest = path.stat().st_size, sha256_file(path)
        if size != asset["bytes"] or digest.lower() != asset["sha256"].lower():
            raise ValueError(f"physical release asset size/hash mismatch: {asset['name']}")
        verified.append({"name": asset["name"], "bytes": size, "sha256": digest})
    return {"schema": "TITAN_V45_HASH_AUDIT_V1", "scope": "manifest_and_available_physical_assets",
            "manifest_sha256": sha256_file(manifest), "declarations_valid": True,
            "declared_assets": len(payload["assets"]), "physical_assets_verified": verified,
            "missing_physical_assets": missing, "all_physical_assets_verified": not missing,
            "require_models": require_models,
            "limitations": ["Metadata validation alone does not verify missing physical files.",
                            "Hash agreement does not certify clinical validity or waveform equivalence."]}


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
        if source.stat().st_size == 0:
            raise ValueError(f"empty release asset: {asset.name}")
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
    validate_release_manifest_hashes(payload)
    manifest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    sums = [f"{row['sha256']}  {row['name']}" for row in asset_rows]
    sums.append(f"{sha256_file(manifest)}  {manifest.name}")
    sha256sums.write_text("\n".join(sums) + "\n", encoding="utf-8")
    return payload
