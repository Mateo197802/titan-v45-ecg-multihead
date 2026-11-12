# CODE signal contract and development ablations

This is a new within-source development study. It does not replace the historical
[PR #6](https://github.com/Mateo197802/titan-v45-ecg-multihead/pull/6) estimates.
The [publisher archive](https://zenodo.org/records/4916206) and the
[published preprocessing source](https://github.com/antonior92/ecg-preprocessing/blob/439bc1bafde571feee9e79e86f475ae9ee37d9e4/ecgprep/preprocess.py#L60-L94)
distinguish the resampled archive from native acquisition. The stored input is
4096 samples at 400 Hz per lead (10.24 s represented); acquisition frequency and
gain are not certified for individual records by the HDF5 matrix. We use the
documented archive lead order and do not infer a record-specific physical gain.

The frozen contract accepts 581/581 zero borders (2934 observed samples, 7.335 s)
or the long forms with 0/0 or 48/48 borders (center 4000 observed samples, 10 s).
The pipeline rejects ambiguous duration, all-zero and flat traces, then applies
a zero-phase 0.05--45 Hz Butterworth bandpass and polyphase resampling to 125 Hz.
Neither convolutions nor descriptor computation sees artificial padding. The two
length buckets have 917 and 1250 samples. Per-lead z-score and robust shared
gain are separate registered variants. Synthetic tests check timing of P/QRS/T,
ST direction, and preservation of a linear limb-lead relationship. These tests
do not establish quantitative clinical morphology agreement on real ECG.

## Executed data QC

Job `33689` completed (`0:0`) with all 18 sealed archives. The source metadata
covered 345,779 ECG and 233,770 patients. The deterministic bounded plan selected
21,933 ECG; 20,958 survived. The 975 exclusions were 745 ambiguous duration,
52 flat lead, 41 all zero, 127 redundant exact copies within a partition and 10
records in cross-partition exact-copy groups (all removed). There were zero
shared patient identifiers between partitions. The 992 PR #6-selected patients
retained by this design are all in training, not in validation/calibration/test.
Waveform matching is exact float32 equality on the observed CODE window; it is
not exhaustive equivalence detection or proof of cross-institution isolation.
See the [cohort CSV](evidence/EXTERNAL_DATA_MANIFESTS_SUMMARY.csv) and
[sanitized audit receipt](evidence/PATIENT_AND_SIGNAL_LEAKAGE_AUDIT.json).

| Split | ECG | Patients | 7.335 s ECG | 10 s ECG |
|---|---:|---:|---:|---:|
| Training | 9869 | 7808 | 5924 | 3945 |
| Validation | 3088 | 2426 | 1881 | 1207 |
| Calibration | 3080 | 2435 | 1876 | 1204 |
| Reserved evaluation | 4921 | 3891 | 3061 | 1860 |

The provider annotations are parsed at bank construction for assignment and
aggregate QC. Candidate fitting and selection do not read the calibration or
test manifests, and there is no test performance available to select on.
Reference claims are concordance with publisher flags, not clinical adjudication.

## Executed frozen controls

Job `33691` completed (`0:0`) with both released heads and original thresholds.
The [60 aggregate rows](evidence/SIGNAL_PROCESSING_ABLATIONS.csv) include matched
duration strata and [a file seal](evidence/VALIDATION_BASELINES_RECEIPT.json).

| Profile | Normalizer | Macro-F1 | Macro-AUPRC |
|---|---|---:|---:|
| P6 | Per-lead z-score | 0.329181 | 0.338307 |
| P8 | Per-lead z-score | 0.319402 | 0.354452 |
| P6 | Robust shared gain | 0.195716 | 0.199189 |
| P8 | Robust shared gain | 0.231454 | 0.205763 |

The normalizer comparison is paired on 3088 validation ECG. It is not a causal
estimate of padding alone and cannot be compared numerically with the historical
PR #6 cohort as if the patient sample were identical. In the per-lead arm, P6
sinus bradycardia had 35 TP and 595 FP, P8 had 43 TP and 855 FP; these operating
points are particularly weak at the observed prevalence. No thresholds were
re-tuned for the released controls.
