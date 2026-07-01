# Contributing

Contributions must preserve the frozen profile contracts, artifact hashes, and evaluation definitions.

1. Create a focused branch and add tests before changing behavior.
2. Run `python -m pytest` and `python -m ruff check .`.
3. Do not commit model weights, raw ECG records, credentials, absolute paths, or private identifiers.
4. Keep validation data names, class orders, thresholds, and metric definitions explicit.
5. Keep Primary8, Primary6 diagnostic, and Primary4 as separate release profiles.

Changes to class order, thresholds, profile hashes, or canonical metrics require a new profile and documented evidence. Existing contracts are immutable.
