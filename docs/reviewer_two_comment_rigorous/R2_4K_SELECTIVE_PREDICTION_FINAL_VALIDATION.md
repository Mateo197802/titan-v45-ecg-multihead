# R2-4k: Selective prediction utility

> How are estimated “Quarantine Rate”, “Pre-Quarantine Accuracy”, “Pre-Quarantine Accuracy”? Explain this in the methodology section.

**IMPLEMENTATION_VERIFIED; EXPERIMENT_COMPLETED for the new policy.** CEDIA job 33799 recomputed every native route from scores and frozen class thresholds; no reference enters the per-ECG decision. P8/P4 cuts are 0.037162775/0.014417143. The two cuts were fitted to coverage on separate SPH components, not on LUDB or on held reference values. The primary emits both original outputs if both score and both margins meet their cutoffs; otherwise it emits neither. Technical inability to score is distinct from abstention.

Historical June disposition: **WITHDRAW_HISTORICAL_CLAIM**. These are November score-only decisions, not an original quarantine estimate, human review or clinical referral. The reviewer's repeated term is quoted as written; we do not assume that a missing historical post-quarantine result exists.

## Utility on fixed denominators

Coverage is accepted/scored ECGs, also reported against all enrolled ECGs. Baseline and accepted risk are membership FP+FN per known ECG–endpoint opportunity, not multiclass ECG accuracy. Withheld risk uses the same original predictions counterfactually; withheld positives are neither emitted FN nor TP. Reported PPV/NPV are only for observed source references; a missing LUDB statement is not a negative. SPH mapped absence is not independent clinical adjudication.

| Cohort | Rule | Accepted/scored ECGs | Known emitted | Accepted risk | Withheld risk | Withheld positives |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| SPH | no_abstention | 12869/12869 | 115821.0 | 9.53% | not estimable | 0.0 |
| SPH | frozen_joint | 10391/12869 | 93519.0 | 9.00% | 11.78% | 740.0 |
| SPH | absolute_threshold_distance | 10391/12869 | 93519.0 | 9.22% | 10.86% | 749.0 |
| SPH | negative_mean_binary_entropy | 10391/12869 | 93519.0 | 8.88% | 12.29% | 1108.0 |
| SPH | random_equal_coverage | 10391/12869 | 93519.0 | 9.53% | 9.53% | 661.2 |
| LUDB | no_abstention | 200/200 | 924.0 | 20.78% | not estimable | 0.0 |
| LUDB | frozen_joint | 152/200 | 697.0 | 19.94% | 23.35% | 80.0 |
| LUDB | absolute_threshold_distance | 152/200 | 696.0 | 19.54% | 24.56% | 82.0 |
| LUDB | negative_mean_binary_entropy | 152/200 | 687.0 | 18.49% | 27.43% | 90.0 |
| LUDB | random_equal_coverage | 152/200 | 702.2 | 20.78% | 20.78% | 77.0 |

Random results are expectations, hence fractional opportunities. Primary paired contrasts use patient/exact-waveform components and a conservative 98.75% interval across two contrasts and two cohorts. The random expected risk equals the all-scored risk; the two primary comparisons have identical risk estimates under that definition.

- **SPH:** difference -0.54 pp, simultaneous interval [-0.63 pp, -0.44 pp]; 2628 original errors (161 FN, 2467 FP) and 19674 original correct known opportunities withheld. Emitted: 337 FN, 8077 FP. 645 ECGs contained at least one withheld known positive. 0 technically unscored ECGs; 0 scored endpoint references unknown.
- **LUDB:** difference -0.84 pp, simultaneous interval [-2.86 pp, +1.05 pp]; 53 original errors (43 FN, 10 FP) and 174 original correct known opportunities withheld. Emitted: 99 FN, 40 FP. 47 ECGs contained at least one withheld known positive. 0 technically unscored ECGs; 1476 scored endpoint references unknown.

The original joint policy need not dominate simpler uncertainty rankings. The JSON includes tied-score risk–coverage curves, AURC, score Brier/ECE, signed-margin reliability and adverse endpoint effects. None of these alternatives was adopted by choosing the best retrospective result.

| Cohort | Joint AURC | Raw distance AURC | Entropy AURC | Break-even λ | Joint cost at λ=.25 | No-abstention cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| SPH | 8.71% | 8.88% | 9.28% | 11.78% | 12.08% | 9.53% |
| LUDB | 16.31% | 16.55% | 14.26% | 23.35% | 21.19% | 20.78% |

The full scored denominator charges one unit for each emitted error plus λ for each withheld known opportunity. It never counts a withheld opportunity as correct. The break-even λ is the fraction of withheld known opportunities that would have been wrong. This sensitivity grid is not a clinical cost model, and unknown references or technical failures are not silently scored as successes.

Neither SPH nor LUDB was newly unseen when this analysis was specified. Different cohort mappings limit portability. A significant result on either cohort would not establish a clinically useful reduction on a new independent population. See the [partial cascade experiment](R2_4K_CASCADE_EXPERIMENT.md) for a separate actual second stage.

## Endpoint effects of the frozen rule

| Source/endpoint | Known positives | FN emitted | Positive withheld | Full sensitivity | PPV accepted | NPV accepted |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| SPH/P8:AFIB | 347 | 10 | 63 | 78.96% | 85.89% | 99.90% |
| SPH/P8:SB | 1375 | 103 | 291 | 71.35% | 71.87% | 98.86% |
| SPH/P8:STACH | 366 | 20 | 68 | 75.96% | 75.14% | 99.80% |
| SPH/P8:RBBB | 359 | 10 | 75 | 76.32% | 53.00% | 99.90% |
| SPH/P8:PAC | 256 | 69 | 78 | 42.58% | 18.14% | 99.30% |
| SPH/P8:PVC | 521 | 83 | 123 | 60.46% | 61.28% | 99.16% |
| SPH/P4:ASMI | 44 | 11 | 13 | 45.45% | 2.40% | 99.88% |
| SPH/P4:LVH | 111 | 25 | 18 | 61.26% | 2.06% | 99.65% |
| SPH/P4:IMI | 55 | 6 | 11 | 69.09% | 1.45% | 99.92% |
| LUDB/P8:AFIB | 15 | 1 | 3 | 73.33% | 78.57% | 99.26% |
| LUDB/P8:SB | 24 | 1 | 4 | 79.17% | 39.58% | 99.01% |
| LUDB/P8:STACH | 4 | 4 | 0 | 0.00% | not estimable | 97.32% |
| LUDB/P8:NSR | 142 | 33 | 38 | 50.00% | 89.87% | 52.86% |
| LUDB/P8:RBBB | 4 | 1 | 0 | 75.00% | 100.00% | 0.00% |
| LUDB/P8:PAC | 7 | 4 | 3 | 0.00% | not estimable | 0.00% |
| LUDB/P8:1AVB | 10 | 5 | 3 | 20.00% | 100.00% | 0.00% |
| LUDB/P8:PVC | 7 | 1 | 3 | 42.86% | 100.00% | 0.00% |
| LUDB/P4:ASMI | 0 | 0 | 0 | not estimable | not estimable | not estimable |
| LUDB/P4:LVH | 108 | 49 | 26 | 30.56% | 100.00% | 0.00% |
| LUDB/P4:IMI | 0 | 0 | 0 | not estimable | not estimable | not estimable |
| LUDB/P4:ISC_ | 0 | 0 | 0 | not estimable | not estimable | not estimable |
