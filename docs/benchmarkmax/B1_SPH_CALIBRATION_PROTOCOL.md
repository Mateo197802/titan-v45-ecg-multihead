# B1 SPH Calibration Diagnostic

**Status:** frozen before B1 calibration metrics are computed. The V4.5 SPH
baseline has already been observed; this is exploratory V4.6 development, not
an untouched or confirmatory test. No manuscript, V4.5 checkpoint, V4.5 score,
threshold or historical result is changed.

## Question

Can a simple monotone probability recalibration of the frozen V4.5 scores
improve probability quality on patient-held-out SPH records, and what operating
point trade-offs appear when an F1 threshold is selected on a separate set of
patients? This does not test whether a new ECG representation or specialist
improves performance, and it cannot establish external or clinical validity.

## Frozen Inputs And Targets

The protocol consumes the V4.5 full-population prediction ledger, SPH metadata,
V4.5 frozen protocol, scoring receipt and normalized aggregate. Their SHA-256
values are pinned in
[`sph_b1_calibration.json`](../../configs/benchmarkmax/sph_b1_calibration.json).
The runner rejects any mismatch and reconciles the saved V4.5 confusion counts
before fitting a calibrator. Private record IDs, patient IDs and per-record
scores stay in CEDIA.

The six targets are P4 ASMI, IMI and LVH; P8 PAC; and P6 PVC and RBBB. They use
the original code mappings and frozen thresholds. A positive means the
corresponding code is present on the ECG. A missing code is not adjudicated
disease absence. PAC/PVC are record-level ECG statements, not beat detection.
The three P6 rhythm endpoints AFIB, SB and STACH are not recalibrated; their
saved scores and decisions remain the protected baseline and are not altered.

## Patient-Grouped Nested Evaluation

Five deterministic outer folds are assigned by SHA-256 of a fixed namespace,
seed and patient ID. In each outer fold, its patients are evaluation-only for
that fold. Among the remaining patients, a second deterministic hash assigns
three quarters to calibration fitting and one quarter to threshold tuning.
The approximate full-cohort proportions are 60% fit, 20% threshold tuning and
20% out-of-fold evaluation. No patient crosses these roles within a fold; all
ECGs belonging to that patient stay together. Labels do not affect assignment.

For each target and fold, positive-slope Platt scaling fits an intercept and
slope to the logits of the frozen probabilities by unweighted record-level
binary log loss. The slope is bounded to `[0.05, 20]`, the intercept to
`[-20, 20]`, and logits are clipped using epsilon `1e-6`. There is no class
reweighting, search, isotonic fit, model training, threshold change to V4.5,
or result-driven method selection. Failure to fit or a missing class in any
role stops the run instead of silently dropping that fold.

Two thresholds are selected independently in the threshold-tuning patients:
one on raw scores and one on Platt scores, each maximizing F1 over the distinct
observed tune scores. Ties select the highest threshold. Those thresholds are
applied only to that fold's out-of-fold patients. A Platt score of `0.5` is
also reported as a descriptive reference operating point, not a clinical
threshold or recommendation. The saved V4.5 labels are reported separately;
this preserves the existing P8 fallback and prevents it from being conflated
with a threshold-only policy.

## Metrics And Uncertainty

For every target, report the source record/patient denominator and positive
support; the saved V4.5 decision baseline; raw-score nested-CV results; Platt
nested-CV results; and Platt-at-0.5 results. Metrics include confusion counts,
accuracy, sensitivity, specificity, PPV, NPV, F1, AUROC, average precision,
Brier score and 10-bin equal-width ECE. Threshold and Platt-slope ranges and
per-fold support are included so small positive groups remain visible.

The paired 2,000-replicate percentile bootstrap resamples patient clusters in
the out-of-fold predictions and reports calibrated-minus-raw differences for
all ten operating and probability metrics listed above. Its intervals are
conditional on the fold-specific calibrators; it does not refit them and does
not estimate transfer to an independent institution.
Point metrics and intervals are exploratory because all SPH outcomes were
previously inspected in the V4.5 transfer analysis. The threshold objective
is an engineering diagnostic only; it has no declared clinical utility.

## Execution And Interpretation

Run the committed SLURM wrapper on a CEDIA CPU partition. The aggregate receipt
is written outside both Git checkouts with mode `0600`; only after its schema,
hashes, denominator and privacy checks pass may the aggregate be added to this
PR. The runner must reconcile the original V4.5 confusion counts exactly.

Even if calibration improves Brier/ECE or a development operating point, this
does not establish a new V4.6 specialist, validate disease status, justify a
clinical threshold, restore SPH as an untouched test, or support a confirmatory
external claim. Any V4.6 model trained or selected using SPH still requires a
different eligible source for confirmatory evaluation.
