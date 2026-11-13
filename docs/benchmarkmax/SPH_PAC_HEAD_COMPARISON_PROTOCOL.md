# SPH PAC Head Comparison

**Status:** frozen protocol for an exploratory V4.6 development experiment.
The protocol is not evidence of external validation. It must be committed before
the head-fitting run and must not be changed after inspecting holdout metrics.

## Question and Scope

Compare the frozen V4.5 P8 PAC score with a new V4.6 unweighted L2 logistic
head and five predeclared single-hidden-layer MLP sensitivity seeds on frozen
V3F ECG representations for the presence of SPH ECG diagnostic statement `30`
(atrial premature complex[es]). The MLP seeds are sensitivity replicates, not
an architecture search; none will be selected as a winner. This is an
exploratory adaptation experiment on SPH, which has already been scored and
inspected in the V4.5 transfer work. A patient split within SPH does not make
the source independent, unseen, external, or confirmatory.

The protocol does not evaluate beat-level PAC events, incident disease,
clinical utility, a clinical decision threshold, or a new backbone. Absence of
code 30 means that the statement was not recorded for that ECG; it is not an
adjudicated disease-negative reference. Code `31` (nonconducted atrial
premature complexes) remains distinct and is not pooled into the positive
class. Before signal exclusions, the frozen source inventory must reconcile to
539 code-30 records and 4 code-31 records; the runner aborts if the dictionary
or these supports differ. Code-31-only records have code 30 not recorded and
remain visible in a separate aggregate count. Only this PAC endpoint is
included; the frozen P8 PAC probability is a historical single-output
comparator, not a new P6/P8/P4 profile evaluation.

## Frozen Inputs and Data Gates

The machine-readable specification is
[`sph_pac_head_comparison.json`](../../configs/benchmarkmax/sph_pac_head_comparison.json).
It pins SHA-256 values for the SPH metadata, diagnostic dictionary, waveform
archive, public source-integrity inventory, and public V3F backbone. The
inventory checksum is
`8321abf1d91f0a97ae65b8e9d3a47ba4f5460055ac7780fd84ad2cc86efd2cf7`; it records
25,770 valid waveforms and 168 exact duplicate groups with 168 excess records.
The frozen V4.5 P8 comparator uses only PAC probabilities from the private,
label-blind full-population scoring ledger (SLURM job `32668`). Its ledger
SHA-256 is `4a3a1e61b1784e06190d5caaa089fca04ef84792acb3a5f9fc1af3f9c1173462`,
receipt SHA-256 is
`8abdc5f6561fc3fea77eeb68e8aa34bc2d02396cad9c2e9fbeea70b4188dac92`, and P8
specialist SHA-256 is
`b30cb2bbb45f1231c93ff1c196aa966b57b49831cadb296131c0283e7b0ceb02`. The
runner verifies those hashes, receipt source hashes, model linkage, label-blind
status and full-scored denominator before use. The row-level ledger remains
private in CEDIA.
The runner rechecks those duplicate totals from the raw signal bytes and aborts
if they differ. It also verifies the exact source population (25,770 ECGs,
24,666 patients), the dictionary descriptions for codes 30 and 31, the Git
commit, protocol/configuration/runner/verifier/wrapper hashes,
dependency-archive hashes, and declared compute runtime. Any mismatch stops
the run.

Waveform inference is label-blind: before the first model inference the runner
reads only `ECG_ID` and sample count from metadata. It does not parse patient
IDs or diagnostic statements until inference and the source-waveform audit
have completed. The archive must contain each indexed ECG exactly once; unsafe
paths, unexpected file types, invalid HDF5 shape/dtype, nonfinite values,
unsupported durations, all-flat signals, or preprocessing failures are
counted or cause a hard failure as specified by the runner.

Exact duplicate signals are detected before joining diagnostic labels by
SHA-256 of the canonical little-endian float64 raw array. Every ECG in any
exact-duplicate group is excluded from fitting and evaluation. This conservative
rule avoids assigning an identical signal to separate patients or partitions.
Near duplicates, duplication against other datasets, and whether V3F training
included any SPH-derived information are not certified by this experiment.

SPH HDF5 does not document physical ECG units as mV. The runner reports
unitless raw amplitude peaks and applies only finite-value / technical signal
checks; it does not invent an mV threshold or choose an amplitude cutoff from
model outcomes. The source's amplitude scale is therefore not physically
calibrated by this analysis.

## Preprocessing and Frozen Representation

The existing reconstructed rhythm preprocessing is applied consistently to
every technically eligible record: native 500 Hz input; third-order causal
Butterworth bandpass at 0.5-45 Hz per lead; polyphase resampling to 125 Hz;
per-lead z-scoring within each 10-second model window with a standard-deviation
floor of `1e-6`; and the recovered rhythm-window schedule of 10 seconds with a
5-second stride and 2-second context padding. The exact historical loader was
not recovered, so this is a new, explicitly reconstructed pipeline and is not
represented as an exact replay of historical preprocessing.

The public V3F backbone is loaded from its exact release checkpoint, strict
state-dict loading is required, and all backbone parameters remain frozen in
evaluation mode. For each record, all eligible window transformer tokens are
pooled into one 1,280-dimensional vector by concatenating their token mean and
token maximum. The logistic head and all five MLP seeds receive the same
feature matrix. Morphology features are not used. The train-partition feature
mean and population standard deviation are used to standardize all partitions;
dimensions with standard deviation below `1e-12` use a scale of one.

Raw signals, row-level embeddings, IDs, labels, scores, and predictions are
never written to the repository or the aggregate report. The learned PAC head
weights are stored with mode `0600` in CEDIA only and are not included in the
public release by this protocol.

## Patient Partitions and Fit Rules

Use the already-frozen label-blind SHA-256 patient assignment from the SPH
feasibility audit:

- train: hash bucket 0-69;
- development: 70-84;
- exploratory holdout: 85-99 (the former feasibility audit's calibration
  bucket).

The namespace is `TITAN-V46-SPH-DEV-SPLIT-V1:`, seed `197802`, and the bucket is
the first 64 SHA-256 digest bits interpreted as a big-endian integer modulo
100. All ECGs for a patient remain in one partition, and labels do not affect
assignment. The report will publish record and patient denominators and
statement-positive supports for every partition. Training stops rather than
silently omitting a partition if either statement-present or
statement-not-recorded examples are absent.

The frozen V4.5 P8 PAC score uses its original membership threshold `0.45`; it
is not refit or recalibrated. The V4.6 logistic baseline uses `C=1.0`,
unweighted mean binary log loss, and an L2 penalty on coefficients only, fitted
by SciPy L-BFGS-B with 1,000 maximum iterations and `ftol=1e-12`. Each MLP has
one hidden layer of 192 units, ReLU, dropout `0.25`, unweighted
`BCEWithLogitsLoss`, AdamW, learning rate `0.001`, weight decay `0.0001`, batch
size 512, seeds `197802` through `197806`, maximum 200 epochs, and patience 20.
Development average precision controls early stopping. There is no class
weighting, resampling, model search, feature selection, or holdout feedback.

Each model's binary operating threshold is selected only on development data
by maximizing F1 over its unique observed probabilities; ties choose the
highest threshold. It is an engineering comparison threshold, not a clinical
threshold. The exploratory holdout is never used to fit weights, stop training,
or choose thresholds.

## Metrics and Uncertainty

On one common exploratory holdout, report the complete denominator,
statement-present and statement-not-recorded counts, TP/FP/TN/FN, accuracy,
sensitivity, specificity, PPV, NPV, F1, AUROC, average precision, Brier score,
and 10-bin equal-width ECE for the frozen P8 score, logistic head and every MLP
seed. The P8 score uses its frozen `0.45` threshold; each new head uses its own
development-only F1 threshold. Report all results, including adverse, null or
unestimable results, without selecting a best seed. Use paired, unstratified
percentile bootstrap intervals of whole patient clusters with 2,000 replicates
and NumPy PCG64 seed `197813` for logistic-versus-P8, each MLP-versus-P8 and
each MLP-versus-logistic comparison. Report valid and invalid replicate counts.
Intervals condition on the fitted models and do not quantify between-source
uncertainty.

The runner writes a private aggregate receipt and private head artifact in
CEDIA. A separate verifier checks hashes, denominators, confusion totals,
scope wording, privacy flags, and schema before an aggregate-only result is
copied to GitHub. No result is complete until the SLURM receipt, output hashes,
test suite, and independent aggregate verification all agree.

## Interpretation Boundary

This split is held out only from this prespecified V4.6 PAC-head fit; it is not
blind to the broader research project. The cohort was previously observed in
V4.5, all outcomes are within one institution, and V3F's historical source
exposure is not fully certified. A positive finding would show only
patient-disjoint exploratory discrimination of SPH ECG statements under the
reconstructed pipeline. It cannot establish clinical disease detection,
independent generalization, or replacement of an external validation cohort.
