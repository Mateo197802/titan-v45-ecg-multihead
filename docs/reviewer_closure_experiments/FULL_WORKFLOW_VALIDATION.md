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
| PTB Diagnostic v1.0.0; one ECG | 549 / 549 scored; 290 source subjects | Separate infarct-territory versus healthy-control comparisons, not complete clinical workflow validation. |

The PTB-XL cached subset is measurably enriched, not a random draw from
its metadata denominator. For example, it contains 252/252 compatible
Paced positives and 1,699/6,549 explicit Normal-only controls. See the
[coverage audit](OTHER_CLASS_VALIDATION.md#ptb-xl-reference-availability-not-performance).
Do not use cached operating-point estimates as population predictive values.

The PTB Diagnostic enrollment is 290 actual subject keys in the verified
RECORDS manifest. The [provider data description](https://physionet.org/content/ptbdb/1.0.0/#data-description)
also says 290; its news blurb says 294. Use the manifest denominator,
not the announcement. PTB Diagnostic describes recordings from a Berlin
cardiology service on a PTB prototype; [PTB-XL](https://physionet.org/content/ptb-xl/1.0.3/#background)
describes a Schiller archive acquired by PTB. This differentiates the
sources and recording protocols, but supplies no cross-release patient
linkage or proof that the historical models were unexposed.

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

### LUDB whole release versus nested restricted subset

[Job 33720](../../outputs/results/reviewer_closure_experiments/ludb_fixed_policy_and_reference_aggregate.json)
joined references after the scoring and routing seal. All 200 ECGs remain
in each full-release denominator. The restricted subset includes any ECG
with at least one positive compatible reference for that profile; it is
not a reproduction of the original specialist panel.

| Profile | Restricted ECGs | Endpoints supported in both denominators | Full macro-F1 | Restricted macro-F1 |
|---|---:|---|---:|---:|
| P6 | 59 | AFIB, SB | 0.6949 | 0.8778 |
| P8 | 188 | AFIB, SB, NSR | 0.7075 | 0.7407 |
| P4 | 108 | None with both reference polarities | Not estimable | Not estimable |

LUDB provided 142 principal sinus-rhythm references, 55 other recognized
principal rhythms and 3 unknowns for the P8 NSR contrast. This is not a
Normal ECG or disease-free label. P4 LVH had 108 positive and 92 unknown
references; named infarct territories and ISC_ were not evaluable there.
P8 PAC had 7 positive and 193 unknown references. These are not negative
controls and cannot contribute to specificity, PPV or NPV for those
endpoints. The aggregate reports route-specific confusion and intervals
where support permits. No endpoint is promoted from one polarity alone.

### PTB Diagnostic: separate pathology-reference cohort

[Job 33737](../../outputs/results/reviewer_closure_experiments/ptb_diagnostic_transport_aggregate.json)
scored every eligible ECG before joining reference values, with no technical
non-scoring. The 549 ECGs represent 290 source subjects and 290
subject/exact-signal components. Native P4 ASMI and IMI decisions used
unchanged published cutoffs. A separate ALMI/ILMI comparison applies
previously trained PTB-XL heads without tuning on PTB Diagnostic. It does
not create a second routing stage.

| Endpoint and score | Positive ECGs / subjects | Explicit control ECGs / subjects | Unknown ECGs | TP/FN/FP/TN | F1 (cluster 95% interval) |
|---|---:|---:|---:|---|---|
| ASMI, original P4 | 77 / 27 | 80 / 52 | 392 | 63/14/20/60 | 0.788 (0.672-0.870) |
| IMI, original P4 | 89 / 30 | 80 / 52 | 380 | 66/23/21/59 | 0.750 (0.632-0.833) |
| ALMI, experimental PTB-XL head | 43 / 16 | 80 / 52 | 426 | 21/22/1/79 | 0.646 (0.523-0.771) |
| ILMI, experimental PTB-XL head | 53 / 22 | 80 / 52 | 416 | 22/31/1/79 | 0.579 (0.345-0.764) |

The provider's clinical header territories and explicit controls are
stronger references for these specific contrasts than a missing ECG
statement, but not a blinded independent re-adjudication. The controls
are repeated across endpoints; do not sum the rows as unique subjects.
Other diagnoses and compound/unresolved territories remain unknown,
so PPV and NPV are conditional on an enriched two-polarity subset.
This experiment supplies neither representative clinical prevalence nor
references for the remaining rhythm and pathology routes.

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
