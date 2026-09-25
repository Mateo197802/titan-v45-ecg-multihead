# Results

Canonical evidence is separated by scope and method. JSON and CSV files are sanitized copies or deterministic derivations of frozen reports. Generated experiments must not overwrite canonical files.

[`release_evidence_verification.json`](release_evidence_verification.json) is the checked-in result of recalculating Primary8, Primary6 diagnostic, and Primary4 metrics from the per-record evidence. It records line-ending-normalized input SHA-256 values and model-asset SHA-256 values. Recreate it with `python scripts/evaluation/verify_release_evidence.py --output outputs/results/release_evidence_verification.json`; run `python -m pytest` to check the repository, including that the snapshot matches the current evidence.
