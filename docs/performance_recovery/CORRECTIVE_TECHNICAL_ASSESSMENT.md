# TITAN V4.5 corrective weight study

## What the audit established before training

- CEDIA job `33825` loaded the sealed PR #10 model strictly (291 state entries,
  58,437,362 parameters) and reproduced all development validation scores
  from the previous diagnostic with max absolute difference 0. The gradient
  probe covered a sample of each observed CODE length (917 and 1,250 samples
  per lead). Each probe had 16,992,199 active parameters in the first phase,
  no disconnected or nonfinite active gradients, no gradients on frozen
  parameters, and zero supervised gradient on the deliberately masked cell.
  This rejects the tested wiring failures, not every possible training bug.
- The CODE bank uses 12 provider-ordered leads at 400 Hz. Chapman/CPSC
  validate WFDB names and physical units, reorder to the same canonical
  leads and convert to mV before extracting a centered 10 s window at 500 Hz.
  The banks use the same zero-phase 0.05-45 Hz bandpass, 125 Hz target and
  per-lead normalization. CODE strips the recognized padding; short ECGs
  are not padded to 10 s. Acquisition systems and reference semantics remain
  different, and exact historical input equivalence is not implied.
- The same patient, exam and exact waveform keys did not cross CODE
  train/validation/calibration. The PR #6 eligibility predicate is not its
  actual roster; only already authorized development keys were checked.
  Chapman provider group proxies, record identities and exact waveform keys
  are disjoint between the supplied training and validation banks. CPSC has
  no certified patient keys; SB and STACH remain masked.
- A mismatch between optimization and operating requirements is directly
  visible: PR #11 ranked checkpoints primarily by AP, but its higher-AP
  finalist lost F1 and failed four safeguards. The present study uses held-out
  patient folds within development to measure decision constraints before
  selecting an epoch. Final cut fitting uses the separate calibration bank.

| CODE validation | Incumbent AP | Incumbent F1 | Best guard-feasible F1 on those same scores |
|---|---:|---:|---:|
| AFIB | 0.601837 | 0.582677 | 0.584416 |
| SB | 0.453495 | 0.495726 | 0.529412 |
| STACH | 0.597271 | 0.642424 | 0.671053 |
| RBBB | 0.729745 | 0.726457 | 0.748815 |
| 1AVB | 0.369299 | 0.453333 | 0.503704 |

The last column is a descriptive validation oracle; no thresholds from it
are used for deployment. Even these optimistic classwise cuts average 0.6075,
below 0.70. The score ordering, not just the chosen cut, therefore limits
performance in this bank. It does not isolate the backbone as the cause.
AFIB and SB missed positives were, on average, 0.448 and 0.496 below the
existing decision thresholds, respectively. For SB on Chapman, AP 0.651744
and an operating point with sensitivity >= 0.20 and PPV >= 0.30 coexist with
0.0906 sensitivity under the incumbent CODE cut. This supports a
source-dependent operating-point problem, not equivalence of labels,
calibration transport or clinical generalization.

The retrospective probe (`33829`) fitted fixed regularized linear readouts
using CODE training only. On Chapman SB, the frozen embedding readout
achieved AP 0.767994 versus 0.651744 for the incumbent head and 0.545738
for the seven descriptors alone. On CODE validation SB it improved AP
from 0.453495 to 0.473103. The backbone therefore carries usable SB
information; the readout and calibration warrant investigation before
changing the architecture. The same probe did not improve CODE validation
AP for AFIB (0.512167 vs 0.601837) or 1AVB (0.365586 vs 0.369299).
Incumbent AP dropped from apparent training to validation for all three:
AFIB 0.798320 to 0.601837, SB 0.774132 to 0.453495, and 1AVB 0.557472 to
0.369299. These are compatible with overfit and distribution effects,
but do not identify a causal block or rule out reference differences.
The probe did not alter the frozen fit roster, selection or thresholds.
It also verified all five physical release weight files.

## Corrective training contract

No new network topology. A frozen copy of the same-seed PR #10 model marks
hard positives and hard negatives **only on training batches**. Supervised
loss gives those AFIB, SB and 1AVB cells extra weight. A logit penalty
preserves STACH and RBBB behavior. The shared head, late Transformer and
late ResNet blocks update progressively. CODE-only and CODE + Chapman use
the same contract, with patient weights and source-specific positive weights.
There is no P-wave/PR detector, heart-rate proxy supervision, or edit to
published weights. The earlier unsuccessful full-depth, focal and
asymmetric runs are not blindly repeated.

The first audit invocation (`33824`) failed before computation with
`TypeError: diagnose() got an unexpected keyword argument 'output'`. The
corrected CLI ran as `33825`; this is an execution error, not a model defect.
The [protocol](CORRECTIVE_PROTOCOL.json) was sealed before the successful
diagnosis and the training allocation.

## Outcomes on matched development records

Job `33826` completed all six fits (two arms, three seeds, three epochs
each) in 20 minutes and 5 seconds. Job `33827` checked all six checkpoint
hashes, calibrated the retained epochs on the separate 3,080-ECG bank
using per-endpoint Platt scaling, then sealed the finalist before scoring
Chapman or CPSC. The CODE-only arm passed all five class guards in one of
three seeds; CODE + Chapman passed them in zero of three. The winner was
the CODE-only median selection-F1 seed `20261112`, epoch 2:
24,000,479 trainable parameters and checkpoint SHA-256
`a02dd24b8664c1c8357deea48660114cd7a65d7193a94d225ececbdc91ed60cc`.
The three-seed OOF selection F1 was 0.555587 (sample SD 0.013445)
for CODE only and 0.558770 (SD 0.006762) for CODE + Chapman. The
guard-based ranking is not equivalent to maximizing this fold-average F1.

| CODE validation (3,088 ECGs; 2,426 patients) | Incumbent | Corrective | Paired difference [95% CI] |
|---|---:|---:|---|
| Macro-F1 | 0.580124 | 0.582916 | +0.002792 [-0.013190, +0.021799] |
| Macro-AUPRC | 0.550330 | 0.539431 | -0.010898 [-0.029527, +0.005529] |
| Brier | 0.017123 | 0.012591 | See per-class paired output |
| ECE | 0.015397 | 0.004389 | See per-class paired output |

The new candidate did not exceed the earlier calibration-only F1
of 0.583840. That calibration-only policy failed the SB sensitivity guard;
the new candidate passed it. Versus the original incumbent:

| Endpoint | Sensitivity A to C | PPV A to C | F1 A to C | FP A to C |
|---|---:|---:|---:|---:|
| AFIB | 0.627 to 0.610 | 0.544 to 0.529 | 0.583 to 0.567 | 31 to 32 |
| SB | 0.547 to 0.623 | 0.453 to 0.402 | 0.496 to 0.489 | 35 to 49 |
| STACH | 0.779 to 0.794 | 0.546 to 0.562 | 0.642 to 0.659 | 44 to 42 |
| RBBB | 0.810 to 0.820 | 0.659 to 0.656 | 0.726 to 0.729 | 42 to 43 |
| 1AVB | 0.618 to 0.673 | 0.358 to 0.363 | 0.453 to 0.471 | 61 to 65 |

AFIB sensitivity did not improve. SB recovered four true positives, but
at the cost of fourteen FP. 1AVB recovered three true positives and
added four FP, so its error objective was not achieved. STACH and RBBB
were preserved within the frozen limits.
SB was the only guard that failed in all five other seeds/arms; one of
those also failed 1AVB. That makes SB stability, not another unconditioned
architecture sweep, the first technical follow-up.

The CODE-only finalist scored 0.5570 vs 0.5262 macro-F1 on 700 Chapman
ECGs (five endpoints). The five-class CI is intentionally absent: 1AVB
had only 11 positive records, below the frozen support rule. On 1,596
CPSC ECGs, the three comparable endpoints improved from 0.8063 to 0.8250
(paired delta +0.01876, ECG-level 95% CI [+0.00825, +0.02995]). CPSC
does not have authenticated patient keys; neither source is a new
independent evaluation. CODE uses patient bootstrap; Chapman uses
provider group proxies where endpoint support allows it.
On Chapman, SB sensitivity remained poor (24/265 to 28/265); false
positives went from 0 to 1. The transfer gain did not resolve SB.

**Decision: do not promote.** Class safeguards for the selected seed,
calibration, and descriptive source guard passed. Target F1, positive
paired gain, three-seed class safeguards, and independent confirmation
did not pass or were not evaluated. HEEDB was not accessed. No valid
alternative cohort was identified under the
[eligibility criteria](INDEPENDENT_COHORT_ELIGIBILITY.md). P4, historical
cascade, class coverage and historical provenance are separate and unchanged.

The [fits](corrective_evidence/CORRECTIVE_FITS.json),
[paired intervals](corrective_evidence/CORRECTIVE_PAIRED_INTERVALS.csv),
[decision](corrective_evidence/CORRECTIVE_DECISION.json), and
[job ledger](corrective_evidence/CORRECTIVE_SLURM.csv) are reproducible
without exposing patient identifiers. New checkpoints and row-level
predictions remain in CEDIA.

For a next experiment, validate a prespecified SB readout and calibration
on development with provider-label concordance and real heart-rate
references. For 1AVB, require reliable P/QRS delineation references before
adding PR features. New independent confirmation needs an authorized,
previously unused institution with five compatible endpoints and
verifiable patient keys. No new experiment was selected after seeing
these results.
