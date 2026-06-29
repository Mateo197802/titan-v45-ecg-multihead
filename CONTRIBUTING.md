# Contributing

Contributions must preserve the frozen profile contracts and scientific claim boundaries.

1. Create a focused branch and add tests before changing behavior.
2. Run `python -m pytest` and `python -m ruff check .`.
3. Run `python scripts/artifacts/audit_publication.py --root .`.
4. Do not commit model weights, raw ECG records, credentials, absolute paths, or private identifiers.
5. Label external data as `external-dev` unless it was locked before all model and threshold decisions.
6. Never relabel Primary6 as Primary8 or project acceptance as metric-gate success.

Changes to class order, thresholds, profile hashes, or canonical metrics require a new profile and documented evidence. Existing contracts are immutable.
