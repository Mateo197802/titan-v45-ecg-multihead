"""Verify the fixed membership-score decision identity on all retained P8 records."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from titan_v45.evaluation.decision_policy import audit_saved_membership_policy


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        report = audit_saved_membership_policy(args.root)
    except (KeyError, OSError, TypeError, ValueError) as exc:
        print(f"Saved membership audit failed: {exc}", file=sys.stderr)
        return 1
    text = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if report["all_decisions_reconstructed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
