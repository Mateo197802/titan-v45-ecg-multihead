# Frozen SPH Model-Transfer Protocol

## Pre-performance amendment

The first full scoring attempt, CEDIA job 32665, stopped at its P4 threshold
contract check before creating a prediction ledger. A metadata-only inspection
of the checkpoint in job 32667 established that its ASMI threshold is stored
as `0.6699999999999999`, not the rounded JSON value `0.67`; the other three
P4 values agree. The configuration is amended to the exact checkpoint value.
No SPH model-performance result was produced or consulted before this amendment.

**State:** frozen before any SPH model-performance result is queried. The
machine-readable companion is
[`sph_frozen.json`](../../configs/external_validation/sph_frozen.json). The
public Git commit containing both files is the preregistration point; run
receipts record its full commit and the configuration SHA-256. Do not amend
that commit or tune any choice using SPH results.

## Purpose and Boundaries

This is a frozen-weight transfer evaluation on the versioned SPH ECG dataset.
It is not a clinical validation, prospective study, or certification that
SPH was untouched by every historical training stage. SPH is attributed to
Shandong Provincial Hospital, distinct from the explicitly named development
sites found so far. Historical pretraining and tuning manifests are incomplete;
the bounded signal-signature comparison against retained Chapman/Shaoxing/
Ningbo and PTB-XL fold-10 assets does not certify complete independence.

The purpose is to measure transfer on compatible, statement-level endpoints
and to expose coverage and failure denominators. No overall P6, P8, or P4
accuracy is defined because the source reference ontology does not support
every output class. Do not describe an absent SPH code as absence of clinical
disease.

## Frozen Inputs

Use the complete SPH V1 source acquired from the versioned Figshare collection:
25,770 ECG metadata rows, 24,666 source patient IDs, the publisher dictionary,
and the corresponding HDF5 TAR. Exact SHA-256 values for `code.csv`,
`metadata.csv`, and `records.tar.gz`, the source-only inventory hash, and the
pre-performance audit hashes are in the JSON config. The public repo contains
aggregate audits only; signals, patient/ECG identifiers, candidate-match rows,
and prediction ledgers remain in CEDIA.

Attempt every metadata ECG. A signal is technically eligible only when its
archive member and metadata ID reconcile, its HDF5 layout contains the expected
`ecg` dataset, it is finite and has 12 leads, and its 500-Hz length is within
the source-supported 10-to-60-second range. Record malformed, missing,
nonfinite, all-flat, or otherwise unusable signals as explicit technical
states; never assign them a negative prediction. The inventory observed
lengths of 5,000 to 28,000 samples (10 to 56 seconds), but the scoring receipt
and final flow report, not that range observation, determine final coverage.
Unreadable members, metadata/archive mismatches, unsupported duration, invalid
HDF5 layout, non-finite signals/features, flat signals, and non-finite model
outputs retain distinct failure states in the sealed ledger and aggregate.

The stored dtype is float16. HDF5 has no physical-unit attribute, so amplitudes
are reported as native stored values; do not claim mV conversion. The fixed
per-lead z-score is gain-invariant for the tested scaling factors. The native
minimum record lead standard deviation is above the preprocessing floor even
after a 0.001 scale factor, so no source record crosses the existing `1e-6`
prefilter branch from that scale change. No amplitude threshold or conversion
is to be introduced.

## Duplicate and Independence Controls

Keep all technically eligible SPH ECGs in primary point estimates, including
exact repeats. There are 168 exact duplicate waveform groups (168 excess ECGs,
336 ECGs total); every group is within one SPH patient ID, so the current exact
duplicate graph has 24,666 patient components. Twenty-five exact groups have
different primary-code sets. Do not resolve those conflicts by choosing one
row or one code.

For each endpoint, report a prespecified sensitivity analysis that removes
every member of an exact-waveform group only when the binary presence of that
endpoint's reference code disagrees within the group. The primary analysis
retains all rows. Bootstrap clusters are connected components of SPH patient
IDs linked by exact waveform hashes; if any exact waveform crosses SPH patient
IDs, those patients are one resampling unit. This does not link SPH patients
to patients at another institution.

Before scoring, compare standardized waveform signatures against only the
retained Chapman/Shaoxing/Ningbo rhythm and PTB-XL fold-10 pathology release
packages. Candidate signatures and record links remain private in CEDIA; only
aggregate pair counts are publishable. The screen is limited to those retained
assets and the specified first-window transform. It does not compare every
historical V3F/V3AG pretraining/fine-tuning input, does not establish patient
identity across sites, and cannot certify full historical independence. Exact
SPH duplicates are assessed; approximate waveform duplicates outside the
predefined quantized-signature screen are not certified absent.

## Frozen Models and Profiles

Run all three release profiles without training, checkpoint reselection,
threshold tuning, recalibration, or label-based routing:

- **P6 diagnostic:** V3F backbone with the V3P e008 Primary6 specialist;
  class order `AFIB, SB, STACH, RBBB, 1AVB, PVC`; mean logits across rhythm
  windows, sigmoid after aggregation, then the six frozen thresholds.
- **P8 candidate:** V3F backbone with the V3Q Primary8 candidate specialist;
  class order `AFIB, SB, STACH, NSR, RBBB, PAC, 1AVB, PVC`; mean per-window
  sigmoid membership, then the eight frozen thresholds. If no threshold is
  crossed, use the existing top-1 fallback. Count this separately; it is not
  quarantine or human review.
- **P4 pathology:** V3AG backbone with the calibrated Primary4 specialist;
  class order `ASMI, LVH, IMI, ISC_`; its four checkpoint thresholds and
  multilabel decisions are unchanged. It has no fallback.

The shared backbone definition is frozen by the implementation hashes and
uses 12 input leads, 14 rhythm outputs, 7 pathology outputs, 10 morphology
features, `d_model=640`, 9 transformer layers, 10 attention heads, and stage
channels `[96, 192, 384, 768]`. P6/P8 share V3F; P4 uses the separate V3AG
backbone. Specialist checkpoints, release manifest, hidden-width tensors,
trainer-feature archive, and every implementation file are hash-pinned in the
config and execution receipt.

## Signal and Window Processing

Use the committed reconstructed waveform path; it is not represented as the
missing historical loader. Read the source 12-lead, 500-Hz HDF5 array without
physical-unit conversion. Preserve the declared lead order and mask. Apply the
source-backed third-order 0.5-to-45-Hz Butterworth bandpass with causal
`lfilter`, polyphase resampling to 125 Hz, the existing lead-wise normalization
and deterministic context padding, and the fixed `12 x 1250` model window.
The ten morphology features are generated by the hash-pinned candidate
implementation. Rhythm signal-event features come from the two pure feature
functions extracted from the hash-pinned recovered trainer archive.

P4 uses the fixed first ten seconds represented in its 12-second context. P6
and P8 use the frozen ten-second window schedule with five-second stride and
the existing terminal-window rule. Aggregate every generated window using
the corresponding profile contract; never select a window or an exclusion by
reference label or model score. The score job reads only `ECG_ID` and sample
count from SPH metadata. It seals a label-blind ledger before the separate
evaluation job reads diagnostic codes. Inference runs in evaluation mode with
gradients disabled, a fixed seed, deterministic PyTorch algorithms, cuDNN
benchmarking off, TF32 disabled, and the pinned cuBLAS workspace configuration.
The scoring receipt records the runtime settings and exact device.

## Diagnostic Correspondence

Reference positives are the presence of an eligible documented ECG statement
in the publisher's primary-code dictionary, not a separately adjudicated
clinical diagnosis. Multiple primary statements may coexist. A negative means
only that the target statement was not recorded. The exact code dictionary
hash and machine-readable mapping are frozen in the config.

Primary evaluable endpoints:

| Profile | Class | SPH primary code | Scope |
| --- | --- | ---: | --- |
| P6 | AFIB | 50 | AF statement on this ECG; not incident AF |
| P6 | SB | 22 | Sinus bradycardia statement |
| P6 | STACH | 21 | Sinus tachycardia statement |
| P6 | RBBB | 106 | Complete right bundle-branch block statement |
| P6 | PVC | 60 | Ventricular premature-complex statement; not beat detection |
| P8 | AFIB | 50 | Same statement-level target as P6 |
| P8 | SB | 22 | Same statement-level target as P6 |
| P8 | STACH | 21 | Same statement-level target as P6 |
| P8 | RBBB | 106 | Same statement-level target as P6 |
| P8 | PAC | 30 | Atrial premature-complex statement |
| P8 | PVC | 60 | Same statement-level target as P6 |
| P4 | ASMI | 165 | Anteroseptal MI ECG statement; no acuity inference |
| P4 | LVH | 142 | ECG LVH statement; not imaging-confirmed hypertrophy |
| P4 | IMI | 161 | Inferior MI ECG statement; no acuity inference |

Do not count code 105 (incomplete RBBB) as code 106, code 31 (nonconducted
atrial premature complexes) as code 30, code 1 (normal ECG) as a definitive
NSR reference, or code 82 (prolonged PR) as adjudicated first-degree AV block.
Codes 145/146 (ST/ST-T deviation) do not establish the `ISC_` target. Do not
report these as primary endpoints or silently pool them into positives.

## Endpoints, Denominators, and Statistics

Report the complete source-to-output flow: metadata rows, archive members,
scored ECGs, technical exclusions and inference failures by reason, missing
signal/metadata states, and per-profile coverage. Report rhythm window counts, P8 fallback count,
empty decision sets, and per-class prediction counts. No class, profile,
unscored row, or empty set becomes `Other` or a quarantine event. No historical
quarantine policy is available; report the rate as not assessed, not zero.

For each endpoint, report the full-source positive and negative reference
supports, scored positive and negative supports, unscored-source count,
confusion counts, accuracy, sensitivity, specificity, PPV, NPV, F1, AUROC,
average precision, Brier score, and 10-bin equal-width ECE. Undefined
class-conditional metrics and their denominators remain explicit. Do not
calculate pooled full-profile accuracy across incompatible references.

Use 2,000 unstratified percentile bootstrap replicates at the patient-component
level, fixed PCG64 seed `197813` plus the endpoint's fixed index in the config;
report 95% percentile intervals and valid/invalid draws for every metric. The
point estimates remain record-level. The sensitivity analysis for
endpoint-discordant exact duplicate groups has its own denominator and
patient-cluster intervals. Do not tune a threshold, mapping, or exclusion in
response to these results.

## Frozen Aggregate Figures

Generate only these three figure families from the aggregate endpoint report:
full-population P6/P8/P4 coverage and reconciled flow counts; endpoint-level
sensitivity, specificity and AUROC with patient-component 95% intervals; and
the endpoint-specific F1 comparison between the all-row primary analysis and
the frozen discordant-exact-duplicate sensitivity analysis. Do not draw a
pooled profile score or use record-level outputs. Write each as PNG and PDF
using the pinned plotting script and rendering environment in the config.

## Publication and Privacy

Publish the frozen protocol/config, code, tests, aggregate control audit,
aggregate endpoint report, aggregate figures, model/data/control hashes, CI
results, and CEDIA job receipts. Keep raw SPH signals, identifiers,
record-level scores, duplicate links, and patient-cluster assignments in the
restricted CEDIA workspace. Preserve the pre-SPH historical outputs without
rewriting them. These results do not retroactively prove the original
historical loader, split isolation, cascade, or quarantine rates.
