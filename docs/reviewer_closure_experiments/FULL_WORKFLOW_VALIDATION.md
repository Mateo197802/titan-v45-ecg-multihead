# Full workflow validation (R1-2)

The reviewer requested all routes, original prevalences, quarantine rates,
false negatives and predictive values, not an extrapolation from the selected
95.19% rhythm accuracy and 80.09% macro-F1. The evidence answers different
parts of this request in different cohorts. These cohorts are not pooled.

## Complete scoring and same-score contrasts

| Source and analysis unit | Eligible / scored | What the denominator establishes |
|---|---:|---|
| SPH v1; one ECG, published P6/P8/P4 | 25,770 / 25,770 per profile | Entire SPH source inventory. 24,666 source patient IDs and 25,602 exact signal signatures. Compatible statement prediction, not adjudicated disease. |
| LUDB v1.0.1; one ECG, published P6/P8/P4 | 200 / 200 per profile | Entire publisher release, without reference-based selection for scoring. Deliberately assembled source; not a natural-prevalence clinic population. |
| PTB-XL bridge; one ECG | 19,601 metadata eligible / 6,205 available and scored | Limited development bridge using folds 1-9; no fold 10 and no claim of complete cohort inference. |
| PTB Diagnostic v1.0.0; one ECG | 549 verified source records / 290 source subjects | Eligibility for separate infarct-territory versus healthy-control comparisons, not complete clinical workflow validation. |

[SPH 33399](../../outputs/results/reviewer_experiments/population-contrast_33399_aggregate.json)
measures the effect of restriction on the same scores and mapped reference
endpoints. The restricted sets use compatible positive statements rather than
the historical specialist panel membership.

| Profile | Full-source macro-F1 | Restricted ECGs | Restricted macro-F1 | Difference (95% interval) |
|---|---:|---:|---:|---:|
| P6 | 0.7083 | 5,523 | 0.9057 | +0.1974 [0.1900, 0.2050] |
| P8 | 0.6622 | 5,925 | 0.8553 | +0.1931 [0.1858, 0.2007] |
| P4 | 0.0388 | 415 | 0.7278 | +0.6891 [0.6511, 0.7246] |

Those aggregate files retain per-endpoint confusion counts, operating-point
statistics, rank metrics, and source-specific prevalence. For example, full
SPH P6 PVC PPV is 905/(905+1,375), and full SPH P4 ASMI PPV is
56/(56+2,219). Neither is clinical PPV and neither can be extrapolated to
another source. The 13,905 SPH Normal-only controls are not an NSR annotation.
In LUDB, mutually exclusive principal rhythms provide explicit endpoint
contrasts; incidental or missing annotations do not establish negatives.

## What actually ran

The published classifiers produced their native threshold sets and top-1
outputs. An empty set or P8 top-1 fallback is not a clinical referral or
quarantine. The separately defined joint abstention wrapper was executed
once per ECG, without seeing reference labels, and logged accepted,
abstained, or technically unscored. No second-stage model or human review
received abstentions. Per-endpoint positives are partitioned into true
positive calls, emitted misses, withheld outputs, and technical failures;
counterfactual baseline misses among withheld positives are separately
counted. See [selective validation](SELECTIVE_PREDICTION_VALIDATION.md).

## Claim boundary

Retain the original panel performance as a selected-denominator result.
Add the full-source, fixed-model comparisons as new experiments, with the
reference definition and all flow counts. Neither the June parent population,
historical cascade, nor a representative cohort with compatible references
across all routes was established. Even complete scoring cannot solve those
three problems. A prospective or well-documented retrospective consecutive
cohort, actual route execution, and independently adjudicated positives and
negatives would be needed for the unrestricted clinical claim.
