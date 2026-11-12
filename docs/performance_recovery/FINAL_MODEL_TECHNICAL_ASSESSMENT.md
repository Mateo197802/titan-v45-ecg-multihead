# TITAN V4.5 performance recovery

## Scope and custody

Five binary endpoints: AFIB, SB, STACH, RBBB and 1AVB. This is an experimental
continuation of the Transformer + ResNet model, not a replacement for released
P6/P8 or a study of P4. The [protocol](MODEL_PERFORMANCE_RECOVERY_PROTOCOL.json)
was frozen publicly at commit `93cabfa4210f6b67f8fcd2901dfd0c2d3b589128`
before CEDIA scoring. Its SHA-256 is
`4d17cf25bf380454277b8e0f7584377370379bcef3b65431a728ea2ca0d0fa9f`.

CODE development: 9,869 train ECGs / 7,808 patients; 3,088 validation ECGs /
2,426 patients; 3,080 calibration ECGs / 2,435 patients. No intersection of
patient keys, exam keys, or exact observed-waveform hashes across these
partitions. Reapplying the PR #6 eligibility predicate on these allowed keys
found 992 eligible training patients and zero in validation and calibration.
This is not an authenticated membership comparison against the PR #6 test
roster, which was not opened. The examined PR #6 and PR #10 test manifests,
scores and waveforms were not opened or used during recovery. The PR #10 test
F1 of 0.602658 and AP of 0.579463 are historical, from a different partition,
and not the comparator for the new development metrics.

The 12-lead signal contract uses observed 7.335 s or 10 s CODE windows from
400 Hz input, without feeding archive padding to the model. Chapman/CPSC
inputs are center windows of 10 s at 500 Hz. The preprocessing applies a zero-phase
0.05-45 Hz bandpass and resamples to 125 Hz before the per-lead or shared-gain
normalization arm. This yields 917 or 1,250 samples per lead for CODE.

## Incumbent failure analysis

- AFIB validation: 22 false negatives among 59 positives at the incumbent cut.
  Sensitivity was 29/38 on short and 8/21 on long ECGs; the pattern does not
  support attributing the errors to short records. Among records with
  confident QRS estimates, sensitivity was 13/23 at 60-100 bpm and 12/15
  above 100 bpm. These are small, overlapping descriptive strata. Spectral
  proxies do not prove noise, morphology differences or causal mechanisms.
- SB validation: 53/3,088 positive CODE ECGs versus 265/700 in the sampled
  Chapman validation bank. This is a difference between sampled supports,
  not population prevalence. Only 15/53 CODE SB positives met the QRS
  confidence rule; 13/15 of those were below 60 bpm. At the incumbent cut,
  CODE SB had 29 TP, 24 FN and 35 FP; Chapman SB had 24 TP, 241 FN and 0 FP.
  Never assign a diagnostic reference from an estimated rate.
- 1AVB validation: 61 FP and 21 FN at the incumbent cut. The short/long FP
  counts were 44/17 over 1,855/1,178 negatives, respectively. This is an
  association, not evidence of abnormal PR conduction or a causal duration
  effect. No PR intervals were measured and P-wave onset was not certified.

The diagnostic [WFDB XQRS](https://wfdb.readthedocs.io/en/latest/processing.html#qrs-detectors)
estimates were made on II and V2 with cross-lead agreement and an RR plausibility
check. They are signal-derived proxies, not adjudicated fiducials. The existing
CODE/Chapman descriptor AUROC (0.906840) is a source-separability observation,
not evidence that the diagnostic model relies on a shortcut.

## Comparison design

**A** is the same incumbent checkpoint and its fixed original operating policy
replayed on the 3,088 CODE validation ECGs. **B** uses the same weights with
calibration-only fitting and classwise restricted thresholds. **C** uses the
selected recovery checkpoint and its own calibration-only policy. Positive
Platt/temperature slopes preserve score ordering; raw AP is reported to
separate discrimination from decision-policy changes. Threshold decisions
are made on raw scores; the calibration mapping is for probabilities.

The initial frozen fits test progressive unfreezing, shared gain normalization,
asymmetric and focal losses, endpoint-specific residual heads, a shared model
with RR/rate and local II/V2 branches, supervised multichannel source mixtures,
and a train-only MIMIC masked-SSL delta. All fitting starts from a frozen,
seed-matched incumbent. The full route, when triggered, unfreezes the feature
path (not the unused released global classifiers) at a lower backbone rate.
Three-seed dispersion includes variation from both initialization and the
recovery fit. Selection uses CODE validation AP; Chapman and CPSC scores do
not choose the checkpoint or the cuts.

## Initial screening

All nine initial arms completed in SLURM jobs `33790`, `33791` and `33792`.
Their best validation raw AP in the frozen screening seed was:

| Arm | Raw macro-AP |
|---|---:|
| Progressive partial, per-lead z-score | 0.551222 |
| Progressive partial, robust shared gain | 0.532909 |
| Asymmetric loss | 0.547763 |
| Focal loss | 0.533126 |
| Independent endpoint residual heads | 0.551016 |
| RR/rate and local conduction branches, hard negatives | 0.544528 |
| CODE + Chapman | 0.561742 |
| CODE + Chapman + CPSC | 0.555242 |
| Train-only MIMIC SSL delta | 0.550567 |

The best partial arm improved on A by 0.011412 raw macro-AP, below the
predeclared 0.02 gate. The improvement was not used to alter the threshold
or add unregistered experiments. Calibration-only B improved CODE F1 from
0.580124 to 0.583840 without changing raw AP, and SB still failed its
validation sensitivity floor (31/53, 58.49%, against 60%).

## Finalist training and selection

The full-depth rule fired in job `33800`. Job `33801` trained 56,684,983
parameters in the waveform-to-endpoint path and attained 0.553368 validation
AP at epoch 4 in the screening seed. The two finalists were then repeated
by job `33803`. After checking the 14 physical checkpoints, curves and
private score files, job `33804` selected CODE + Chapman:

| Family | Seed 20261112 AP | Seed 20261113 AP | Seed 20261114 AP | Mean AP |
|---|---:|---:|---:|---:|
| Full, CODE only | 0.553368 | 0.562451 | 0.555460 | 0.557093 |
| Progressive partial, CODE + Chapman | 0.561742 | 0.566603 | 0.555791 | 0.561379 |

The representative is the median-AP seed 20261112 at epoch 2, with 24,000,479
trainable parameters at that epoch, per-lead z-score normalization, a shared
five-output head and bounded weighted BCE. SHA-256:
`5cd03ef01f88c7bee7760e5165b4abe99706278c564650d4a46314f7c930de92`.
This seal precedes candidate calibration scoring; no model was selected from
calibration performance or held-out test outcomes.

## Operating-point results and decision

| CODE validation, 3,088 ECGs | Macro-F1 | Raw macro-AP | Brier | ECE |
|---|---:|---:|---:|---:|
| A: incumbent weights and thresholds | 0.580124 | 0.550330 | 0.017123 | 0.015397 |
| B: incumbent with new calibration | **0.583840** | 0.550330 | 0.012454 | **0.004671** |
| C: selected new weights with new calibration | 0.565871 | **0.561742** | **0.012422** | 0.005463 |

Grouped calibration selected per-endpoint Platt scaling for B and C.
The selected C improved discrimination by +0.011412 raw AP relative to A,
but lost 0.014253 macro-F1. B had the best F1 at the registered policies,
but still failed the SB validation floor. Neither crossed 0.70.

| Endpoint | Positive ECGs | A sensitivity / PPV / F1 | C sensitivity / PPV / F1 | C guard |
|---|---:|---|---|---|
| AFIB | 59 | 0.627 / 0.544 / 0.583 | 0.542 / 0.571 / 0.557 | Fail: sensitivity below 0.54322; 5 additional FN |
| SB | 53 | 0.547 / 0.453 / 0.496 | 0.585 / 0.408 / 0.481 | Fail: sensitivity below 0.60; 35 to 45 FP |
| STACH | 68 | 0.779 / 0.546 / 0.642 | 0.824 / 0.483 / 0.609 | Fail: PPV below 0.49639; 44 to 60 FP |
| RBBB | 100 | 0.810 / 0.659 / 0.726 | 0.780 / 0.684 / 0.729 | Pass: both within the frozen limits |
| 1AVB | 55 | 0.618 / 0.358 / 0.453 | 0.545 / 0.390 / 0.455 | Fail: sensitivity below 0.56818; 61 to 47 FP but 4 additional FN |

Both B and C passed the Brier/ECE guard. Passing a guard on the calibration
partition was not sufficient: the fixed thresholds were carried to validation
without change. **Decision: no promotion.** Keep the published and prior
incumbent policies unchanged; the new candidate is retained for research.

## Source diagnostics

| Bank | ECGs | Comparable endpoints | F1, A to C | Raw AP, A to C |
|---|---:|---:|---|---|
| Chapman validation | 700 | 5 | 0.526211 to 0.547418 | 0.684369 to 0.768828 |
| CPSC source-excluded for C | 1,596 | 3 | 0.806283 to 0.820686 | 0.863652 to 0.868475 |

C was fitted with Chapman training data. The 700 Chapman validation rows
have nonoverlapping provider group keys, record keys and exact waveform
hashes relative to that training bank, not a new institutional holdout.
C was not fitted with CPSC, but CPSC had historical exposure, and no
validated patient IDs are available. SB and STACH are masked there; the
three-class CPSC macro values must not be compared with five-class CODE or
Chapman values. These source results are descriptive, not external
confirmation. No new institution was scored.

## Reproduction

The [SLURM entry point](../../scripts/cedia/titan_performance_recovery.sbatch)
separates diagnosis, incumbent calibration, fitting, conditional full fitting,
repetition, finalist selection, post-selection calibration scoring and
aggregate reduction. On CEDIA, use the sealed private development banks and
release weights referenced in the protocol; the scripts reject test splits
and hash-check the inputs. The fit receipts preserve the pinned code commit,
parent and output checkpoint hashes, epoch curves, and SLURM job. Exact
checkpoint bytes and row-level scores stay in authorized storage.

Job `33805` scored the candidate calibration partition after the model was
sealed; job `33806` reduced A/B/C metrics and job `33807` assembled the
public evidence. See the [metrics](evidence/DOMAIN_GENERALIZATION_MATRIX.csv),
[guard decisions](evidence/MODEL_PROMOTION_GATES.json),
[training and hashes](evidence/FINETUNING_EXPERIMENTS.csv), and
[SLURM ledger](evidence/SLURM_EXECUTION_LEDGER.csv).

The public delivery can be verified without CEDIA access:

```sh
python scripts/domain_adaptation/verify_recovery_delivery.py docs/performance_recovery/evidence
python -m pytest -q tests/test_performance_recovery.py
```

See the [independent-cohort decision](INDEPENDENT_COHORT_ELIGIBILITY.md) for
the access, endpoint support and historical-exposure limits. A positive
development result alone cannot authorize promotion.
