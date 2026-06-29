from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from titan_v45.artifacts.release import ReleaseAsset, build_release_manifest


def _read_assets(path: Path) -> list[ReleaseAsset]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = csv.DictReader(handle)
        return [
            ReleaseAsset(
                source=row["source"],
                name=row["name"],
                path=row["path"],
                category=row["category"],
            )
            for row in rows
        ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Build release-manifest.json and SHA256SUMS.")
    parser.add_argument("--assets-csv", type=Path, required=True)
    parser.add_argument("--repository", default="Mateo197802/titan-v45-ecg-multihead")
    parser.add_argument("--tag", default="v0.1.0")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--sha256sums", type=Path, required=True)
    args = parser.parse_args()
    build_release_manifest(
        assets=_read_assets(args.assets_csv),
        repository=args.repository,
        tag=args.tag,
        manifest_path=args.manifest,
        sha256sums_path=args.sha256sums,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
