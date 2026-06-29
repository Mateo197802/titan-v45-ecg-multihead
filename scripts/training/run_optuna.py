from __future__ import annotations

import argparse
import importlib


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a resumable TITAN Optuna objective.")
    parser.add_argument("--objective", required=True, help="Import path module:function.")
    parser.add_argument("--study-name", required=True)
    parser.add_argument("--storage", required=True)
    parser.add_argument("--n-trials", type=int, required=True)
    parser.add_argument("--direction", choices=("maximize", "minimize"), default="maximize")
    parser.add_argument("--seed", type=int, default=197813)
    args = parser.parse_args()

    try:
        import optuna
    except ImportError as error:
        raise SystemExit("Install the 'optuna' project extra before running this command.") from error
    module_name, separator, function_name = args.objective.partition(":")
    if not separator:
        raise ValueError("--objective must use module:function syntax")
    objective = getattr(importlib.import_module(module_name), function_name)
    sampler = optuna.samplers.TPESampler(
        seed=args.seed, multivariate=True, n_startup_trials=10
    )
    study = optuna.create_study(
        study_name=args.study_name,
        storage=args.storage,
        direction=args.direction,
        sampler=sampler,
        load_if_exists=True,
    )
    study.optimize(objective, n_trials=args.n_trials)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
