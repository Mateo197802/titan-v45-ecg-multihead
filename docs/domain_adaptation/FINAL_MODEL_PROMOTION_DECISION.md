# Reserved within-CODE comparison and promotion decision

**EXTERNAL_ADAPTATION: FAIL.** The candidate improved the matched five-endpoint
macro-F1 substantially, but did not reach 0.70 and failed prespecified operating
safeguards. **INDEPENDENT_GENERALIZATION: NOT_EVALUATED.** P6 and P8 replacement
is rejected for this candidate; neither published profile is modified. P4 is
not evaluable from CODE labels. R1-1 remains partially addressed.

## Model, population and execution

The winner by three-seed validation macro-AP was partial Transformer + ResNet
(16,992,199 trainable parameters), mean validation AP 0.545022 and F1 0.558114
at 0.5. The median-AP checkpoint from job `33696` used seed 20261112, epoch 5
(validation AP 0.550205, F1 0.582790). [Selection](evidence/CANDIDATE_SELECTION_RECEIPT.json)
was published at [`5060edb`](https://github.com/Mateo197802/titan-v45-ecg-multihead/commit/5060edbf0bc86d4f1596a6596da05bd2fce144b1)
before test inference. [Operating thresholds](evidence/FROZEN_CANDIDATE_THRESHOLDS.json)
were selected only on 3080 ECG from 2435 calibration patients.

Job `33768` scored the three systems once on all 4921 eligible reserved ECG
from 3891 patients. Released P6/P8 retained published thresholds. Candidate and
controls used the same corrected observed signals and evaluation labels.
Job `33769` reduced the sealed private predictions to public aggregates,
including 1000 patient-cluster bootstrap replicates. These CIs condition on
the selected checkpoint and calibration; they do not quantify across-hospital
uncertainty. Individual rows remain in CEDIA.

Job `33772` independently recomputed 546 per-endpoint point estimates and
30 macro-F1 CI endpoints using the same sealed private predictions but a
separate implementation. The maximum absolute point difference was
2.22e-16; all audited macro CI endpoints matched exactly. The term
independent here applies to the calculation, not the institution or cohort.

The execution ledger accounts for 11 completed supervised fits, one masked
SSL fit and 3965 GPU-allocation seconds (1.10 GPU-hours), including control
scoring and cancelled setup time. The study remained within the registered
limits. There was no full-depth training because its gate did not trigger.

| Model | Macro-F1 | 95% CI | Candidate gain and paired 95% CI |
|---|---:|---|---|
| Published P6 | 0.347962 | 0.319967 to 0.374958 | +0.254696 (0.222034 to 0.288306) |
| Published P8 | 0.370366 | 0.339554 to 0.400351 | +0.232291 (0.197721 to 0.268708) |
| Candidate | 0.602658 | 0.564561 to 0.634111 | not applicable |

Macro-AUPRC improved from 0.357411 (P6) and 0.390036 (P8) to 0.579463, and
macro-Brier fell from 0.104780 and 0.095117 to 0.014944. These ranking and
probability metrics complement F1, which also depends on the different
operating-threshold policies. They do not isolate the effect of one training
change or prove clinical calibration.

## What failed and what improved

| Endpoint | Positive ECG | Candidate F1 | Candidate sensitivity | Candidate PPV | Candidate TP / FP / FN |
|---|---:|---:|---:|---:|---:|
| AFIB | 101 | 0.541063 | 0.554455 | 0.528302 | 56 / 50 / 45 |
| SB | 64 | 0.465753 | 0.531250 | 0.414634 | 34 / 48 / 30 |
| STACH | 110 | 0.657040 | 0.827273 | 0.544910 | 91 / 76 / 19 |
| RBBB | 133 | 0.825623 | 0.872180 | 0.783784 | 116 / 32 / 17 |
| 1AVB | 82 | 0.523810 | 0.670732 | 0.429688 | 55 / 73 / 27 |

- **AFIB:** sensitivity fell by 12.87 percentage points versus P6 and 6.93
  versus P8. Both point differences exceed the 5-point guard; the paired
  intervals are -22.34 to -1.98 and -16.00 to +2.31 points, respectively.
- **1AVB:** sensitivity improved, but false positives increased from 27 to 73
  versus P8 and PPV fell by 6.09 points. The point-based precision safeguard
  failed even though the paired interval includes zero.
- **SB:** P8 false positives fell from 1390 to 48, but true positives fell from
  56 to 34. The gain in F1 is not a gain in sensitivity.
- **RBBB and STACH:** RBBB improved both sensitivity and PPV against P6/P8;
  STACH substantially improved PPV while losing one true positive versus each.

Short-window candidate macro-F1 was 0.638063 on 3061 ECG for five endpoints.
The long-window result was 0.565924 on 1860 ECG for four endpoints; SB lacked
the prespecified positive-patient support in that stratum. Do not use these
two macro values as a causal comparison of duration or sum patient strata.

## Evidence boundary

This is patient-disjoint **within CODE** after adaptation on CODE. It is not
independent institutional confirmation or adjudicated clinical validation.
The historical [PR #6](https://github.com/Mateo197802/titan-v45-ecg-multihead/pull/6)
benchmark used a different sample and signal contract and is not overwritten.
HEEDB access and processing approval were not confirmed, so no such data were
acquired. No decision was tuned using this test. A future promoted candidate
would require an authorized new confirmation cohort, explicit compatible
references and new development-only work to protect AFIB sensitivity and 1AVB
precision.

[Per-class results](evidence/EXTERNAL_PER_CLASS_RESULTS.csv) |
[Patient intervals](evidence/PATIENT_BOOTSTRAP_CONFIDENCE_INTERVALS.csv) |
[Promotion checks](evidence/WITHIN_CODE_PROMOTION_DECISION.json) |
[Execution ledger](evidence/SLURM_EXECUTION_LEDGER.csv) |
[Evaluation receipt](evidence/WITHIN_CODE_EVALUATION_RECEIPT.json) |
[Private-score readback receipt](evidence/WITHIN_CODE_INDEPENDENT_READBACK.json)
