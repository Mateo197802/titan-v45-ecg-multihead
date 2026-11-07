"""Diagnose sealed replay margins without changing inputs, scores or thresholds."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from titan_v45.evaluation.replay_diagnostics import build_replay_diagnostics


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pathology-ledger", required=True, type=Path)
    parser.add_argument("--rhythm-ledger", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if any(path.resolve().is_relative_to(ROOT.resolve())
           for path in (args.pathology_ledger, args.rhythm_ledger)):
        parser.error("private ledgers must remain outside the checkout")
    report = build_replay_diagnostics(ROOT, args.pathology_ledger, args.rhythm_ledger)
    with args.output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, indent=2, allow_nan=False)
        handle.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
