from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract the frozen Optuna summary from a JSON report.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    trials = payload.get("trials", [])
    complete = [trial for trial in trials if str(trial.get("state", "")).upper() == "COMPLETE"]
    summary = {
        "objective": "0.6 * Primary8 macro-F1 + 0.4 * Primary4 macro-F1 - missing-class penalties",
        "best_trial": payload.get("best_trial", payload.get("best_trial_number")),
        "best_value": payload.get("best_value"),
        "best_params": payload.get("best_params", {}),
        "trials_total": len(trials),
        "trials_complete": len(complete),
        "promotion_role": "internal_hyperparameter_selection_only",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
