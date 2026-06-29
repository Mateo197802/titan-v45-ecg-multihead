from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from titan_v45.contracts.profiles import CANONICAL_PROFILES
from titan_v45.evaluation.primary import write_canonical_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Write a canonical TITAN V4.5 primary report.")
    parser.add_argument("--profile", choices=sorted(CANONICAL_PROFILES), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_canonical_report(args.profile, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
