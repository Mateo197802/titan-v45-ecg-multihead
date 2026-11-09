# B1 SPH Prevalence Comparator

**Status:** frozen before recomputing the supplementary comparator. This is a
new analysis of the already observed SPH cohort, not an untouched, independent,
confirmatory, or clinical evaluation. It does not change V4.5 weights, scores,
thresholds, labels, historical results, or manuscript files.

## Question And Comparator

The earlier B1 analysis found large Brier and ECE reductions after Platt
calibration, but did not compare either score set with a prevalence-only
predictor. This addendum estimates a constant endpoint probability using only
the calibration-fit patients in each existing outer fold and scores that
constant on the fold's held-out patients. Its fitting patients are exactly the
same patient group used to fit the B1 Platt calibrator. The threshold-tuning
partition and outer-evaluation labels do not contribute to the prevalence
estimate.

The comparator is the unweighted record-level prevalence of the endpoint's
frozen ECG statement code. It is a probability baseline with no ranking or
decision threshold. It is not a clinical disease prevalence estimate.

## Frozen Inputs And Endpoints

The run must verify the original B1 metadata, score ledger, V4.5 protocol,
scoring receipt, normalized baseline aggregate, B1 configuration, B1 runner,
and B1 aggregate SHA-256 values in
[`sph_b1_prevalence_comparison.json`](../../configs/benchmarkmax/sph_b1_prevalence_comparison.json).
It must also reproduce the raw and Platt nested-CV summary metrics from the
published B1 aggregate before calculating comparator results. The six targets
and their mappings are inherited byte-for-byte from the frozen B1
configuration: P4 ASMI/IMI/LVH, P6 PVC/RBBB, and P8 PAC.

The outcome remains presence of an ECG statement code on that ECG. Missing
codes are not clinically adjudicated negatives. PAC/PVC remain record-level
statements, not beat-event detection.

## Assignment And Metrics

Use the same five deterministic patient-grouped folds and fixed seed as B1.
In each fold, estimate prevalence from patients assigned to the B1
`calibration_fit` role outside the outer fold. Score the constant on every
record from the outer-fold patients. Verify that the fit and evaluation patient
sets are disjoint, every source record receives exactly one out-of-fold score,
and both statement classes are present in each fit and evaluation partition.

For raw V4.5 scores, Platt-calibrated out-of-fold scores, and the constant
prevalence scores, compare Brier score, equal-width 10-bin ECE, and log-loss.
AUROC and average precision remain documented by the original B1 report for
raw and Platt scores, but are excluded from this comparator. The prevalence
estimate can differ across outer folds; pooled ranking metrics for these
fold-specific constants could therefore reflect between-fold prevalence
variation rather than within-fold discrimination. No classification metrics
or threshold are assigned to the constant baseline.

Report paired differences as `raw - prevalence` and `Platt - prevalence`.
Negative Brier, ECE, and log-loss differences favor the first method. Use 2,000
paired, unstratified patient-cluster bootstrap replicates for Brier, ECE, and
log-loss, seed `197823 + endpoint_index`, resampling all ECGs from a selected
patient together. The intervals are conditional on the already-fitted
fold-specific Platt and prevalence estimates; neither is refitted inside the
bootstrap. AUROC and average-precision differences are descriptive point
estimates only.

## Execution And Interpretation

Run only from the frozen public checkout in CEDIA's existing `yc_env2`
environment (Python 3.10.18, NumPy 1.26.4, SciPy 1.15.3) on a CPU job. The
aggregate is written outside both Git checkouts with mode `0600`; no record or
patient IDs, per-record scores, or ECG signals may be exported. The public
receipt is eligible for publication only after its hash, source counts,
patient-cluster split, B1 metric reconciliation, and privacy checks pass.

All SPH records and outcomes were previously examined in V4.5 transfer work.
This comparator cannot make SPH independent again, establish clinical truth,
justify a threshold, or satisfy an external-validation request. It only
clarifies whether B1's probability-error results outperform a simple
cross-fitted prevalence estimate on this previously observed development
source.
