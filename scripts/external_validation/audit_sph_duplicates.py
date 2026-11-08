"""Audit exact SPH signal duplicates and native amplitude metadata."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from titan_v45.data.sph_duplicates import audit_sph_duplicates


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--private-index", required=True, type=Path)
    args = parser.parse_args()
    if args.source.resolve().is_relative_to(ROOT):
        parser.error("SPH source files must stay outside the repository")
    if args.output.resolve().is_relative_to(ROOT) or args.private_index.resolve().is_relative_to(ROOT):
        parser.error("SPH audit outputs must stay outside the repository")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    report = audit_sph_duplicates(args.source, args.private_index)
    with args.output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, indent=2, allow_nan=False)
        handle.write("\n")
    args.output.chmod(0o600)
    args.private_index.chmod(0o600)


if __name__ == "__main__":
    main()
