# Evaluation methods and cohort

**Study design:** patient-disjoint held-out evaluation within CODE-15%
following supervised domain adaptation. [CODE-15% v1.0.0](https://zenodo.org/records/4916206)
is a source external to the original TITAN experiment, but the adapted
candidate used supervised CODE training. The unit of prediction is an ECG;
the unit resampled for uncertainty is a patient.

| Admitted partition | ECGs | Patients | 7.335 s delivered | 10 s input |
|---|---:|---:|---:|---:|
| Train | 9,869 | 7,808 | 5,924 | 3,945 |
| Validation | 3,088 | 2,426 | 1,881 | 1,207 |
| Calibration | 3,080 | 2,435 | 1,876 | 1,204 |
| Reserved test | 4,921 | 3,891 | 3,061 | 1,860 |

The [cohort counts](../technical_package/source_snapshot/evidence/EXTERNAL_DATA_MANIFESTS_SUMMARY.csv)
are sealed by the [leakage audit](../technical_package/source_snapshot/evidence/PATIENT_AND_SIGNAL_LEAKAGE_AUDIT.json),
which reports zero patient-key overlap across partitions. The frozen patient
hash assigned 70/10/10/10% buckets before patient caps, ECG caps (two per
patient) and QC. Validation, calibration and test excluded patients meeting
the PR #6 selection predicate. The train count of 992 flagged patients is
predicate-based, not a verified intersection with the final PR #6 roster.
The waveform duplicate screen used exact observed float32 hashes within CODE;
it does not certify cross-institution patient independence. Across all four
partitions the QC excluded 41 all-zero, 745 ambiguous-duration, 52 flat-lead,
10 cross-split exact-waveform and 127 within-split duplicate observations.
These are pooled exclusions, not counts solely from the reserved partition.

**Signal contract:** provider lead order I, II, III, aVR, aVL, aVF, V1-V6;
400 Hz, HDF5 rows with 4,096 samples per lead. Symmetric 581/581 all-lead
zero borders leave 2,934 observed samples (7.335 s); 0/0 and 48/48 patterns
use the center 4,000 samples (10 s). These are delivered/used durations,
not a claim about device acquisition duration. Other patterns were excluded.
The selected pipeline applied third-order Butterworth SOS, zero-phase
0.05-45 Hz filtering, polyphase resampling to 125 Hz and per-lead z-score
normalization. It grouped 917- and 1,250-sample inputs by length; no synthetic
padding entered the candidate model. It did not infer physical acquisition
gain from the HDF5 amplitude.

**Model and selection:** V3F ECG backbone (1D residual blocks and Transformer),
with a new five-output MLP (LayerNorm, 128 hidden units, SiLU and dropout).
The head uses the pooled embedding, seven observed-window descriptors and
two duration indicators. Selected training used CODE train only, with
masked weighted binary cross-entropy, patient weighting and regularization
toward the initial backbone. The trainable subset included the last ResNet
block and token projection, last two Transformer layers, final norm and
new head: 16,992,199 trainable parameters. The selected checkpoint was
seed 20261112, epoch 5, job 33696; the median validation-AP seed of the
highest mean validation-AP eligible family was locked before test scoring.
Other source/SSL and loss variants are not the selected model.

**Reference and decision:** explicit publisher flags map AF to AFIB, SB to
SB, ST to STACH, RBBB to RBBB, and 1dAVb to 1AVB. Unrecognized values are
masked; the final five comparisons have all 4,921 usable flags per endpoint.
Flags are not independently adjudicated for this study and AFIB is not
incident AF. Candidate cuts in the stated endpoint order were 0.66, 0.87,
0.48, 0.44 and 0.51. Cuts were chosen only on calibration, on a 0.05-0.95
grid, maximizing F1 under sensitivity floors of 0.50 for AFIB/RBBB/1AVB.
No post-hoc probability mapping was fitted for the selected PR #10 system.
P6/P8 used released weights and published class cuts on the same observed
ECGs; their probability/feature paths differ from the adapted MLP. This is
a comparison of complete operating systems, not of weights alone.

**Metrics:** use separate binary confusion counts per endpoint. Sensitivity
is TP/(TP+FN), specificity TN/(TN+FP), PPV TP/(TP+FP), NPV TN/(TN+FN),
F1 2TP/(2TP+FP+FN), accuracy (TP+TN)/(TP+TN+FP+FN). Macro-F1,
macro-AUROC, macro-AUPRC (non-interpolated average precision), mean binary
accuracy, macro-Brier and macro-ECE average five endpoints equally. Brier is
mean squared probability error; ECE uses ten equal-width bins. Bootstrap
used 1,000 patient-cluster draws, seed 20261112, with all ECGs for a sampled
patient kept together and identical draws for paired comparisons. Support
required at least 20 positive and negative patients per endpoint; long-window
SB is not estimable. Short and long macro values cannot be directly compared
as a duration effect because their endpoint rosters differ. Confidence
intervals condition on the frozen checkpoint, thresholds and dataset.
