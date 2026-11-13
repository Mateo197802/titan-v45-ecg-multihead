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
splits, but those splits are not a locked test. The report distinguishes the
open MIMIC-IV-ECG v1.0 machine-report resource, which is not yet reserved or
inspected, from the credentialed MIMIC-IV-ECG-Ext-ICD resource, for which no
author access is confirmed. The public PTB/INCART/MIT-BIH sources do not directly
satisfy the current endpoint contracts.

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
does not establish independent validation or a new V4.6 specialist.

Because B1 did not include a constant-prevalence probability comparator, a
separate, frozen patient-cross-fitted comparison was run against the same
saved scores. It is an exploratory diagnostic on previously observed SPH, not
independent, external, or clinical validation and not a model-selection
result. The [protocol](B1_SPH_PREVALENCE_COMPARATOR_PROTOCOL.md),
[aggregate-only results](B1_SPH_PREVALENCE_RESULTS.md), and receipt are
tracked in the [experiment registry](BENCHMARKMAX_EXPERIMENT_REGISTRY.json).

A separate label-blind scale-sensitivity probe replayed 128 records at 0.5x,
1x and 2x waveform gain. Scores and decisions were invariant to these uniform
scales under lead-wise z-score normalization; this is not physical-unit
certification. See [`SPH_SCALE_SENSITIVITY_RESULTS.md`](SPH_SCALE_SENSITIVITY_RESULTS.md)
and the aggregate-only [receipt](../../outputs/results/benchmarkmax/sph_scale_sensitivity_32761.json).

## PAC Head Pilot

A separate raw-signal pipeline and protocol define an exploratory SPH PAC
statement-head comparison using frozen V3F mean+max token embeddings. The
frozen comparison includes the historical V4.5 P8 PAC score (receipt-linked to
CEDIA job `32668`, threshold `0.45`), a new L2 logistic head, and five fixed
single-layer MLP seeds (`197802`-`197806`) reported individually without
selecting a winner. All new heads use train-only feature scaling,
patient-grouped 70/15/15 assignment, development-only early stopping and
threshold selection, and paired patient-cluster bootstrap comparisons against
P8; each MLP is also compared with logistic regression. The protocol,
configuration, runner, CEDIA SLURM wrapper, privacy verifier, and focused tests
are in the experiment registry. Job `32805` completed on CEDIA using the frozen
protocol and configuration. Its aggregate-only report records average
precision of `0.307` for frozen P8, `0.450` for logistic, and `0.527`-`0.587`
for the five MLP seeds; sensitivity was `0.583`, `0.607`, and `0.476`-`0.631`,
respectively. The holdout contains 84 positive statements, so these values are
exploratory and imprecise. See [SPH PAC results](SPH_PAC_HEAD_COMPARISON_RESULTS.md).
CEDIA jobs `32799`, `32800`, and `32802` failed for runner/configuration
contract mismatches; their private logs, hashes, and failure stages remain in
the registry. Job `32802` completed signal embedding and fit the logistic
baseline; its P8/logistic holdout metric objects existed transiently in memory
but were not emitted, persisted, inspected, or used for selection. It stopped
before MLP fitting, bootstrap comparisons, or artifact/report writing. Job
`32805` used the already-frozen metric choices after code-to-config alignment,
including the protocol's `patience_epochs` key.
The PAC-only job's aggregate, verification receipt, results report and figures
are linked in the registry. Fitted head weights and record-level data remain
private in CEDIA. The held-out SPH subset
is exploratory adaptation on a source observed previously; this is not
independent, external, confirmatory, clinical, or prospective validation and
does not satisfy the external-validation requirement. The pilot is PAC-only,
not a P6/P8/P4 full-profile evaluation. Verify the public aggregate, receipt,
report, and figures using the linked
[SHA-256 inventory](SPH_PAC_HEAD_COMPARISON_32805.SHA256SUMS).

The SPH source does not encode physical units as mV in the audited HDF5
metadata, so the runner reports unitless amplitudes and applies no unsupported
mV gate. Exact duplicate signals are excluded before labels are joined; this
does not certify near-duplicate or cross-dataset training-source independence.

## MIMIC Report Parser

The approved scope is agreement with MIMIC-IV-ECG v1.0 automatically generated
machine-report statements only; these are not adjudicated clinical references.
The deterministic parser in `src/titan_v45/benchmarkmax/mimic_reports.py`
preserves all 18 `report_0..report_17` slots, recognizes four explicit states,
and refuses to load a phrase mapping without corresponding-author approval.
Its empty [mapping template](../../configs/benchmarkmax/mimic_pac_report_mapping.template.json)
is intentionally not executable. Unit tests use synthetic phrases only; they
do not approve real MIMIC terminology. Unmapped negation or qualification cues
near a PAC match fail closed to `uncertain_or_qualified`; phrase matches do not
cross sentence or semicolon boundaries.

Two local, aggregate-only commands are implemented: `audit_mimic_metadata.py`
checks the `record_list.csv` to `machine_measurements.csv` key join, and
`audit_mimic_pac_statements.py` classifies report statements only after that
join is valid and the phrase mapping carries the required author approval. The
statement audit emits input/mapping hashes and aggregate state counts; it does
not emit IDs, paths, report text, row-level labels, or model metrics. Both
commands have only been tested on synthetic fixtures.

No real MIMIC files have been downloaded, parsed, or scored, and no MIMIC
metrics exist. Full waveform acquisition remains blocked until per-user CEDIA quota,
scratch capacity, retention and cleanup are confirmed. The design, endpoint
limits and stop conditions are documented in
[`MIMIC_IV_ECG_MACHINE_REPORT_CONCORDANCE_DESIGN.md`](MIMIC_IV_ECG_MACHINE_REPORT_CONCORDANCE_DESIGN.md).
The current parser implementation does not close external validation and is
not part of the SPH PAC result.
