"""Report aggregate SPH integrity and diagnostic statement counts only."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from titan_v45.data.sph import build_sph_inventory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.source.resolve().is_relative_to(ROOT):
        parser.error("SPH source files must stay outside the repository")
    report = build_sph_inventory(args.source)
    with args.output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, indent=2, allow_nan=False)
        handle.write("\n")


if __name__ == "__main__":
    main()
