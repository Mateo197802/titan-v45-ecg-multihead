from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from titan_v45.evaluation.heads import evaluate_binary_heads


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate classwise binary head probabilities.")
    parser.add_argument("--input", type=Path, required=True, help="NPZ with targets and probabilities arrays.")
    parser.add_argument("--classes", nargs="+", required=True)
    parser.add_argument("--thresholds", nargs="+", type=float, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    arrays = np.load(args.input)
    report = evaluate_binary_heads(
        targets=arrays["targets"],
        probabilities=arrays["probabilities"],
        classes=args.classes,
        thresholds=args.thresholds,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
