# Results

Canonical evidence is separated by scope and method. JSON and CSV files are sanitized copies or deterministic derivations of frozen reports. Generated experiments must not overwrite canonical files.

[`revision_20261107/`](revision_20261107/) contains three native CEDIA aggregates and their byte-level execution receipt. They describe new inference on retained development cohorts, not replacement canonical predictions. See the [scope and reproducing commands](../../docs/frozen-waveform-audit.md).

[`release_evidence_verification.json`](release_evidence_verification.json) is the checked-in result of recalculating Primary8, Primary6, and Primary4 metrics from the per-record evidence. It records line-ending-normalized input SHA-256 values and model-asset SHA-256 values. Recreate it with `python scripts/evaluation/verify_release_evidence.py --output outputs/results/release_evidence_verification.json`; run `python -m pytest` to check the repository, including that the snapshot matches the current evidence.

[`benchmarkmax/sph_b1_calibration_32758.json`](benchmarkmax/sph_b1_calibration_32758.json) is an aggregate-only exploratory calibration diagnostic on previously observed SPH scores. Its protocol, interpretation, CEDIA receipt, hashes, and reproduction commands are documented in [`B1_SPH_CALIBRATION_RESULTS.md`](../../docs/benchmarkmax/B1_SPH_CALIBRATION_RESULTS.md); its PNG/PDF figure hashes are bound in [`sph_b1_calibration_figure_manifest.json`](../figures/benchmarkmax/sph_b1_calibration_figure_manifest.json). It is not independent validation and does not close V4.5 reviewer observations.
