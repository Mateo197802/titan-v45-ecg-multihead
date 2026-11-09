# TITAN V4.6 BenchmarkMax experimental workspace

This branch is a new, separate experimental program. The V4.5 release,
checkpoints, historical results and SPH protocol are not changed. The baseline
SPH scoring and its limitations are documented in [V4.5 PR #3](https://github.com/Mateo197802/titan-v45-ecg-multihead/pull/3)
and its [published aggregate](https://github.com/Mateo197802/titan-v45-ecg-multihead/blob/99b97b9/outputs/results/external_sph/sph_aggregate_32669.json).

SPH performance has already been observed. Any use for calibration, training,
threshold selection or model selection is development/adaptation, not an
untouched external test. No new training, calibration, selection or evaluation
split is claimed by the initial baseline diagnostic. A genuinely separate
eligible final source must be identified and protected before training a new
model intended for a confirmatory external claim; historical data lineage,
patient overlap, signal duplicates, rights and reference compatibility remain
explicit gates.

`scripts/benchmarkmax/audit_sph_baseline.py` reads the sealed CEDIA ledger and
SPH metadata, verifies their hashes and the public baseline aggregate, and
emits only aggregated statement-level confusion counts and 20-bin score
distributions. Binned threshold curves describe the already-observed dataset;
they are not a selected policy, a validation study, or evidence of improvement.
Absence of a coded ECG statement is not adjudicated absence of disease.

The current data, rights, and label-feasibility assessment is recorded in
[`DATA_AND_LABEL_FEASIBILITY_REPORT.md`](DATA_AND_LABEL_FEASIBILITY_REPORT.md).
The SPH metadata can support exploratory development with patient-grouped
splits, but those splits are not a locked test. The report also records that
MIMIC access is not confirmed and that the public PTB/INCART/MIT-BIH sources do
not directly satisfy the current endpoint contracts.
