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

The first V4.6 calibration experiment is frozen in
[`B1_SPH_CALIBRATION_PROTOCOL.md`](B1_SPH_CALIBRATION_PROTOCOL.md) and
[`sph_b1_calibration.json`](../../configs/benchmarkmax/sph_b1_calibration.json).
It uses positive-slope Platt scaling on the already-observed V4.5 scores, with
nested patient-grouped fitting, threshold tuning and evaluation. It does not
train new weights or restore SPH as an external test. Its SLURM runner publishes
aggregate metrics only after exact hash and baseline-confusion reconciliation.

That B1 score-calibration diagnostic has completed on the previously observed
SPH outcomes; see [`B1_SPH_CALIBRATION_RESULTS.md`](B1_SPH_CALIBRATION_RESULTS.md).
It did not train or modify weights, produced no F1 decision improvement, and
does not establish independent validation or a new V4.6 specialist. New-model
training remains blocked on an audited feature pipeline and adequate
development support; an independent final cohort is still unconfirmed.

A separate label-blind scale-sensitivity probe replayed 128 records at 0.5x,
1x and 2x waveform gain. Scores and decisions were invariant to these uniform
scales under lead-wise z-score normalization; this is not physical-unit
certification. See [`SPH_SCALE_SENSITIVITY_RESULTS.md`](SPH_SCALE_SENSITIVITY_RESULTS.md)
and the aggregate-only [receipt](../../outputs/results/benchmarkmax/sph_scale_sensitivity_32761.json).
