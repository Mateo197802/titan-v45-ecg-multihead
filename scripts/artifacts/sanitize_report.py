from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from titan_v45.artifacts.sanitize import sanitize_report_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Sanitize a CSV or JSON report for publication.")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    sanitize_report_file(args.source, args.destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
