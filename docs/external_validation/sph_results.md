# SPH statement-level transfer results

These are ECG-statement comparisons, not clinical diagnoses or incident disease.
An absent statement is not adjudicated absence of disease. Historical training
lineage is incomplete, so full independence is not certified.

Scored ECG: 25,770 / 25,770; technical exclusions: 0; inference failures: 0.
Quarantine was not assessed. Patient-component percentile intervals use 2,000 replicates.

| Endpoint | Positive / negative statements | Sensitivity | Specificity | F1 | F1 95% CI | AUROC |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| P6:AFIB | 675 / 25,095 | 93.04% | 99.55% | 88.76% | 86.92% to 90.38% | 99.87% |
| P6:SB | 2,711 / 23,059 | 82.18% | 95.54% | 74.66% | 73.46% to 75.83% | 96.87% |
| P6:STACH | 725 / 25,045 | 85.24% | 99.27% | 80.94% | 78.62% to 83.08% | 99.19% |
| P6:RBBB | 710 / 25,060 | 96.62% | 95.74% | 55.70% | 53.15% to 58.12% | 98.75% |
| P6:PVC | 1,067 / 24,703 | 84.82% | 94.43% | 54.08% | 52.02% to 56.17% | 95.62% |
| P8:AFIB | 675 / 25,095 | 93.63% | 99.46% | 87.60% | 85.65% to 89.39% | 99.87% |
| P8:SB | 2,711 / 23,059 | 88.38% | 94.66% | 75.60% | 74.35% to 76.71% | 97.95% |
| P8:STACH | 725 / 25,045 | 87.86% | 98.90% | 77.78% | 75.47% to 79.95% | 99.02% |
| P8:RBBB | 710 / 25,060 | 94.23% | 97.12% | 63.68% | 61.10% to 66.04% | 98.96% |
| P8:PAC | 539 / 25,231 | 61.60% | 93.52% | 26.50% | 24.11% to 28.74% | 84.96% |
| P8:PVC | 1,067 / 24,703 | 77.04% | 97.59% | 66.16% | 64.01% to 68.35% | 97.28% |
| P4:ASMI | 91 / 25,679 | 61.54% | 91.36% | 4.73% | 3.51% to 6.09% | 87.62% |
| P4:LVH | 209 / 25,561 | 71.77% | 69.21% | 3.65% | 3.04% to 4.28% | 79.43% |
| P4:IMI | 120 / 25,650 | 89.17% | 75.19% | 3.25% | 2.65% to 3.87% | 90.88% |

P4 F1 and P8 PAC results must not be hidden or compared directly with
historical balanced panels. NSR, 1AVB and ISC_ have no primary compatible
SPH reference in this protocol; no pooled full-profile accuracy is reported.
The [full aggregate](../../outputs/results/external_sph/sph_aggregate_normalized_32669.json)
contains confusion counts, predictive values, calibration metrics, valid
and invalid bootstrap draws, and duplicate-sensitivity analyses. The
[independent point check](../../outputs/results/external_sph/sph_independent_points_32672.json)
recomputes point metrics from restricted inputs. A separate
[bootstrap check](../../outputs/results/external_sph/sph_independent_bootstrap_32677.json)
reproduces six binary-metric intervals, including F1; it does not independently
recalculate AUROC, average precision, Brier or ECE intervals.
