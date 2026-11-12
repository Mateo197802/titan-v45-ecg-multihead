# TITAN V4.5: November reviewer experiments

These are post-study experiments, not a reconstruction of June clinical workflow or
an independent validation. Released weights and historical prediction tables were
not changed. The [execution register](NOVEMBER_EXECUTION.md) documents frozen
protocols and failed attempts. CEDIA retains the individual ledgers and new model
weights; only checked aggregate JSON and receipts are linked here.

## R1-2: Full denominator and diagnostic scope

The reviewer asked for performance beyond the restricted specialist denominator,
including all routes, predictive values at original prevalence and misses among
accepted and quarantined ECGs. The quoted 95.19% rhythm accuracy and 80.09%
macro-F1 do not establish that full workflow.

[Scoring 33355](../../outputs/results/reviewer_experiments/sph_baseline_scoring_receipt_33355.json)
processed **25,770/25,770 SPH V1 ECGs** under each original profile, with zero
technical exclusions, from **24,666 source patient IDs** and **25,602 distinct
exact waveform signatures**. No labels controlled inference. The independent
execution audit [33356](../../outputs/results/reviewer_experiments/sph_repeat_audit_33356.json)
found a byte-identical SPH scoring ledger to the earlier SPH run 32668. This is
repeatability of one pipeline on the same data, not independent generalization.

[33357](../../outputs/results/reviewer_experiments/sph-ece-report_33357_aggregate.json)
reports confusion counts, sensitivity, specificity, precision, F1, AUROC,
average precision, Brier score and ECE with patient-component intervals for 14
mapped profile-endpoints. [33399](../../outputs/results/reviewer_experiments/population-contrast_33399_aggregate.json)
adds NPV, source-statement prevalence, eligibility and call counts by reference
stratum, and the paired effect of restricting the same SPH cohort. The restricted
subset includes every record with at least one mapped statement for that profile;
it is not the historical selected panel. An absent mapped statement is a negative
for statement prediction, not verified absence of disease.

| Profile | Mapped endpoints | Full cohort macro-F1 | Restricted ECGs | Restricted macro-F1 | Restricted minus full, 95% CI |
|---|---:|---:|---:|---:|---:|
| P6 | 5 | 0.7083 | 5,523 | 0.9057 | +0.1974 [0.1900, 0.2050] |
| P8 | 6 | 0.6622 | 5,925 | 0.8553 | +0.1931 [0.1858, 0.2007] |
| P4 | 3 | 0.0388 | 415 | 0.7278 | +0.6891 [0.6511, 0.7246] |

There were 13,905 explicit Normal ECG-only controls, not an NSR reference.
P6 emitted 16,785 empty label sets; P8 used 801 original top-1 fallbacks; P4
emitted 8,343 empty sets. None of these events is an abstention. On all SPH
records, P6 PVC PPV was 0.397 (905 TP, 1,375 FP); P4 ASMI PPV was 0.025
(56 TP, 2,219 FP). A high binary accuracy in a low-prevalence endpoint must not
be interpreted as clinical workflow accuracy.

SPH did not validate NSR, 1AVB or ISC_ under the primary mapping. In the
[PTB-XL bridge 33410](../../outputs/results/reviewer_experiments/ptbxl-bridge_33410_aggregate.json),
6,205 of 19,601 metadata ECGs in folds 1-9 had authorized cached inputs and were
scored. Against explicit SCP positives and Normal-only controls, P6 and P8 1AVB
F1 were 0.938 and 0.967 (1,969 known scored ECGs), and P4 ISC_ F1 was 0.825
(2,046). This selected development inventory does not fill the missing SPH
references, establish clinical ground truth or provide an independent cohort.
Fold 10 was not used in that bridge.

**Disposition: partial.** The November denominator is complete for inference and
for the stated mapped comparisons (R1-2.1). June parent cohort and historical
quarantine outcomes (R1-2.2-3), verified reference coverage for all routes and
end-to-end clinical performance remain unestablished.

## R2-general: Other and auxiliary outputs

The reviewer asked what the excluded and auxiliary outputs actually do, and
requested an Other evaluation. The [released asset audit](RELEASE_HEAD_SUPPORT.md)
separates direct stage supervision from output presence and from inference
performance. The V3F archived loss selects the eight P8 targets for rhythm;
P6 reports six. V3AG instead declares a distinct rhythm subset including Flutter
and Paced. Both declare Pathology4. Auxiliary ALMI, ILMI and LAE scores exist,
but their presence is not proof of direct stage supervision or a deployed route.

[SPH auxiliary 33369](../../outputs/results/reviewer_experiments/auxiliary_33369_aggregate.json)
found released-score AUROC **0.0744** for Flutter (99 positives) and **0.3037**
for LAE (19 positives), each against 13,905 explicit Normal ECG-only controls.
Unknown references were retained in the flow and excluded from those metrics.
The receipt calls the Flutter field a logit; the sealed scorer emits window-mean
auxiliary softmax probability. No additional transform or inversion was applied.
The PTB-XL bridge separately measured threshold-free AUROC 0.818 for ALMI,
0.869 for ILMI and 0.631 for the combined LAO/LAE reference, not isolated LAE.

[SPH Other 33396](../../outputs/results/reviewer_experiments/rhythm-other_33396_aggregate.json)
tested new logistic heads on frozen scores. It split the complete source by
patient/exact-signal component (15,501 train, 5,149 calibration, 5,120 held);
operating points were frozen before held evaluation. Comparator scores are
calibrated auxiliary maxima, not released Other decisions.

| Mapped held endpoint | Known ECGs | Positives | New head F1 | Auxiliary comparator F1 |
|---|---:|---:|---:|---:|
| P6 Other | 2,895 | 141 | 0.647 | 0.092 |
| P8 Other | 2,797 | 43 | 0.625 | 0.030 |
| Flutter | 2,773 | 19 | 0.857 | 0.013 |
| LBBB | 2,772 | 18 | 0.400 | 0.013 |
| 2AVB | 2,764 | 10 | 0.778 | 0.006 |

The P6 union includes PAC; the P8 union does not. Neither treats NSR as an
arrhythmia. Prolonged QT is not LQTS and Paced had no verified SPH mapping.
The 3AVB individual head lacked training/calibration support. Unknown and
discordant exact signals remain visible in the held flows. For example, P8
Other called positive on 147 ECGs whose reference state was unknown; they are
neither verified true positives nor false positives.

[PTB-XL Other 33390](../../outputs/results/reviewer_experiments/pathology-other_33390_aggregate.json)
tested newly fitted heads on authorized sealed Stage A features. Of 390 held
ECGs, 153 had a known reference for the mapped union ALMI/ILMI/LAO-or-LAE;
F1 was 0.939 (46 TP, 6 FN, 101 TN, 0 FP). The other 237 were unknown, including
109 called positive. F1 was 0.900 for ALMI, 0.571 for ILMI and 0.889 for the
LAO/LAE composite on their respective known subsets. These are different models
and cohorts from the released P4 specialist; there is no published P4 decision
head for these endpoints. The full 19,601 metadata denominator and all missing
scoring states are preserved separately.

**Disposition: partial.** Output/supervision boundaries and bounded Other
alternatives have evidence (R2-general.1). They do not validate a comprehensive
Other class or a deployed cascade (R2-general.2).

## R2-3f: Features, real connections and replay

The reviewer requested formulas for ten features, clarification of why Figure 5
shows an arrow only to pathology, and a check of arrow semantics in Figures 5/6.
The [feature contract](MORPHOLOGY_INPUT_CONTRACT.md) specifies every formula,
unit, scaling, missing-input handling and both real model calls in the pinned
reconstructed source. Heuristic width and timing descriptors are not validated
clinical intervals.

[Replays 33469/33470 and contrast 33472](../../outputs/results/reviewer_experiments/replay-contrast_33472_aggregate.json)
repeated both earlier November native ledgers byte-for-byte. Against the
archived historical tables, the result was different:

- **P4:** 962/962 panel observations across 733 ECGs matched for comparison.
  No binary decisions changed, but 836 scores exceeded the frozen 1e-5
  tolerance; maximum absolute deviation was 0.0006194.
- **P6:** 1,643/1,643 archived ECGs scored; no threshold-set or window-count
  changes. One top-1 switched between the same two candidates; its archived
  winner margin was 0.00001994, below the observed score drift on that ECG.
  This diagnoses the rank swap, not the original source of numerical drift.
- **P8:** 2,193/2,193 scored with no top-1, threshold-set or window-count
  changes. This is decision agreement, not a certification of identical scores.

[33473 rhythm](../../outputs/results/reviewer_experiments/morph-sensitivity_33473_rhythm-aggregate.json)
and [33473 pathology](../../outputs/results/reviewer_experiments/morph-sensitivity_33473_p4-aggregate.json)
zeroed only the normalized morphology vector with the weights and thresholds
fixed. Decision fields changed for 37/1,643 P6, 120/2,193 P8 and 8/733 P4 ECGs
on the selected panels. Zero-input perturbation demonstrates dependence of the
implemented decision function, not incremental value after retraining.

**Disposition: partial.** Candidate formula, inputs and wiring are supported
(R2-3f.1); exact original loader identity and strict historical score
equivalence are not (R2-3f.2-3). The new replay does not authenticate historical
specialist metadata (R2-3f.4). Job 33474 sealed both fitted arms before the
released-baseline comparison failed. Evaluation-only recovery 33596 must be
verified before drawing any conclusion about incremental predictive value.

## R2-4k: Executed abstention, not historical quarantine

The reviewer requested the calculation of Quarantine Rate and Pre/Post
Quarantine Accuracy (the original comment repeats “Pre-Quarantine Accuracy”).
The original SPH baseline applied no such policy. [33362](../../outputs/results/reviewer_experiments/selective_33362_aggregate.json)
and [33414](../../outputs/results/reviewer_experiments/joint-selective_33414_aggregate.json)
executed a new retrospective policy on 12,869 held SPH ECGs. Confidence
thresholds came from the disjoint calibration half. No label was used for an
individual routing decision; no second stage or human review was executed.

| Policy | Abstained | Coverage | Baseline mapped macro-F1 | Accepted-only mapped macro-F1 | AURC |
|---|---:|---:|---:|---:|---:|
| P6 | 1,285 | 90.01% | 0.7163 | 0.7517 | 0.0228 |
| P8 | 1,277 | 90.08% | 0.6653 | 0.6980 | 0.0140 |
| P4 | 1,329 | 89.67% | 0.0361 | 0.0377 | 0.2253 |
| Joint P8 and P4 | 2,478 | 80.74% | 0.4555 | 0.4791 | 0.0871 |

Joint acceptance requires both margins to pass; otherwise neither prediction is
emitted. Abstention was **19.26%** (patient-component 95% CI 18.55-19.89%);
technical non-scoring was zero. The mean binary endpoint accuracy was 0.9047
on all held ECGs versus 0.9100 on accepted ECGs; joint selective risk is its
accepted complement, 0.0900. Accepted-only F1 increased by 0.0236 (95% CI
0.0189-0.0283) across the nine mapped endpoints, not across all labels or all
ECGs. P4 alone had no clear improvement (delta CI -0.0009 to +0.0039).

For joint AFIB, 274/347 held statement positives were correctly emitted, 10
were emitted false negatives and 63 received no prediction; 9 of those 63 were
baseline counterfactual misses. For PAC the corresponding counts are 109, 69
and 78 of 256, with 35 baseline counterfactual misses among the abstentions.
The aggregate contains the confusion counts by route, disposition for every
mapped positive class and source strata, risk-coverage curves, and bootstrap
intervals. An abstained positive is neither an emitted FN nor a corrected case.

**Disposition: partial overall; November SPH abstention measured.** The new
aggregate supports a separately dated policy estimate for R2-4k.2. Historical
R2-4k.1 remains not assessed. Neither 0% nor the Plan AE 9.976% can be reported
as an original operational quarantine rate. No historical rubric points were
updated by this report.
