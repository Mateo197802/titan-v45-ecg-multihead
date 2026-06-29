from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Tune deterministic classwise thresholds on internal validation predictions."
    )
    parser.add_argument("--predictions", type=Path, required=True, help="NPZ with y_true and y_prob.")
    parser.add_argument("--classes", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--grid-start", type=float, default=0.05)
    parser.add_argument("--grid-stop", type=float, default=0.95)
    parser.add_argument("--grid-step", type=float, default=0.005)
    args = parser.parse_args()

    import numpy as np

    from titan_v45.training.calibration import tune_binary_thresholds

    payload = np.load(args.predictions)
    classes = tuple(item.strip() for item in args.classes.split(",") if item.strip())
    grid = np.arange(args.grid_start, args.grid_stop + args.grid_step / 2, args.grid_step)
    thresholds = tune_binary_thresholds(payload["y_true"], payload["y_prob"], grid=grid)
    if len(thresholds) != len(classes):
        raise ValueError("class count does not match prediction width")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            {
                "scope": "internal_validation",
                "external_data_used_for_selection": False,
                "classes": classes,
                "thresholds": thresholds,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
