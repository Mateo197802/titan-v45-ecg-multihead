from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from titan_v45.contracts.profiles import CANONICAL_PROFILES
from titan_v45.evaluation.primary import evaluate_primary_predictions


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate top-1 predictions on external-dev data.")
    parser.add_argument("--profile", choices=sorted(CANONICAL_PROFILES), required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    profile = CANONICAL_PROFILES[args.profile]
    rows = list(csv.DictReader(args.predictions.open(encoding="utf-8", newline="")))
    index = {name: position for position, name in enumerate(profile.classes)}
    report = evaluate_primary_predictions(
        y_true=np.asarray([index[row["true_label"]] for row in rows]),
        y_pred=np.asarray([index[row["predicted_label"]] for row in rows]),
        classes=profile.classes,
        scope="external_dev",
    )
    report["claim_boundary"] = "Repeated evaluation; this is external-dev, not external-final."
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
