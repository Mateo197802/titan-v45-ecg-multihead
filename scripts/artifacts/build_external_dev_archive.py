from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Materialize sanitized external-development records and a tar.zst archive."
    )
    parser.add_argument("--manifest", type=Path, action="append", required=True)
    parser.add_argument("--license", type=Path, action="append", default=[])
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    from titan_v45.artifacts.dataset_archive import (
        create_reproducible_tar_zst,
        materialize_external_development_package,
    )

    result = materialize_external_development_package(
        args.manifest,
        args.output_dir,
        license_files=args.license,
    )
    if args.archive is not None:
        create_reproducible_tar_zst(args.output_dir, args.archive)
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(result.__dict__, indent=2) + "\n", encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
