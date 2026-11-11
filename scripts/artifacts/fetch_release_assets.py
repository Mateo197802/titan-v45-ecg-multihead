from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from titan_v45.artifacts.manifest import sha256_file


def select_assets(assets: list[dict], requested_names: list[str] | None) -> list[dict]:
    names_in_manifest = [asset["name"] for asset in assets]
    if len(names_in_manifest) != len(set(names_in_manifest)):
        raise ValueError("release manifest contains duplicate asset names")
    if requested_names is None:
        return assets
    requested = set(requested_names)
    unknown = requested - set(names_in_manifest)
    if unknown:
        raise ValueError(f"unknown release asset names: {', '.join(sorted(unknown))}")
    return [asset for asset in assets if asset["name"] in requested]


def main() -> int:
    parser = argparse.ArgumentParser(description="Download and verify TITAN V4.5 Release assets.")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--asset-name", action="append",
                        help="download only this manifest asset; repeat to select multiple assets")
    args = parser.parse_args()
    payload = json.loads(args.manifest.read_text(encoding="utf-8"))
    for asset in select_assets(payload["assets"], args.asset_name):
        destination = (args.root / asset["path"]).resolve()
        if not destination.is_relative_to(args.root.resolve()):
            raise ValueError(f"asset path escapes root: {asset['path']}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists() or sha256_file(destination) != asset["sha256"]:
            urllib.request.urlretrieve(asset["download_url"], destination)
        if sha256_file(destination) != asset["sha256"]:
            raise RuntimeError(f"downloaded asset hash mismatch: {asset['name']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
