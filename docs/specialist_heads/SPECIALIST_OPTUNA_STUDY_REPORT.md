# Optuna Study Report

**Status: `NOT_RUN` by predeclared design.**

Stage A has a bounded, frozen comparison: three loss formulations and three seeds at one fixed architecture. Georgia, CPSC, and PTB-XL fold-9 internal evaluation are reserved for reporting and cannot select trials or hyperparameters. No new Optuna SQLite database, trial, or search result exists for this experiment.

This does not recover or alter either historical Optuna study. If the fixed comparison is inconclusive and a search is scientifically justified, it requires a separate frozen search space, train/validation-only objective, trial budget, SQLite file, code/config hashes, and a new experiment version before any source-holdout labels are inspected.
