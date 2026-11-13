# Reviewer-Proposed Tables

**For author review only.** These tables are not inserted into the submitted manuscript. Values are read from the linked aggregate JSON files; no patient/ECG rows or identifiers are used.

## SPH ECG-statement endpoints

Each endpoint has 25,770 scored ECG records (24,666 source patients overall), with no unscored records in the frozen receipt. A positive/negative statement is a source-code presence/absence label, not an adjudicated clinical diagnosis. `TP/FP/TN/FN` are ordered as written. Values in parentheses are 95% percentile intervals from 2,000 unstratified bootstrap replicates over connected components of patient IDs linked by exact-waveform duplicates; they are not intervals over independent institutions.

| Endpoint | Source code(s) | Positive / negative | TP / FP / TN / FN | Accuracy (95% CI) | Sensitivity (95% CI) | Specificity (95% CI) | PPV (95% CI) | NPV (95% CI) | F1 (95% CI) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| P4:ASMI | 165 | 91 / 25679 | 56 / 2219 / 23460 / 35 | 91.25% (90.90%-91.61%) | 61.54% (51.14%-71.95%) | 91.36% (91.01%-91.72%) | 2.46% (1.81%-3.19%) | 99.85% (99.79%-99.90%) | 4.73% (3.51%-6.09%) |
| P4:IMI | 161 | 120 / 25650 | 107 / 6365 / 19285 / 13 | 75.25% (74.71%-75.80%) | 89.17% (83.21%-94.34%) | 75.19% (74.64%-75.73%) | 1.65% (1.34%-1.98%) | 99.93% (99.90%-99.96%) | 3.25% (2.65%-3.87%) |
| P4:LVH | 142 | 209 / 25561 | 150 / 7869 / 17692 / 59 | 69.24% (68.68%-69.79%) | 71.77% (65.50%-77.96%) | 69.21% (68.65%-69.78%) | 1.87% (1.55%-2.21%) | 99.67% (99.58%-99.75%) | 3.65% (3.04%-4.28%) |
| P6:AFIB | 50 | 675 / 25095 | 628 / 112 / 24983 / 47 | 99.38% (99.28%-99.48%) | 93.04% (91.01%-94.92%) | 99.55% (99.47%-99.63%) | 84.86% (82.25%-87.30%) | 99.81% (99.76%-99.86%) | 88.76% (86.92%-90.38%) |
| P6:PVC | 60 | 1067 / 24703 | 905 / 1375 / 23328 / 162 | 94.04% (93.74%-94.35%) | 84.82% (82.65%-86.98%) | 94.43% (94.14%-94.73%) | 39.69% (37.61%-41.73%) | 99.31% (99.21%-99.41%) | 54.08% (52.02%-56.17%) |
| P6:RBBB | 106 | 710 / 25060 | 686 / 1067 / 23993 / 24 | 95.77% (95.50%-96.00%) | 96.62% (95.19%-97.85%) | 95.74% (95.48%-95.98%) | 39.13% (36.71%-41.50%) | 99.90% (99.86%-99.94%) | 55.70% (53.15%-58.12%) |
| P6:SB | 22 | 2711 / 23059 | 2228 / 1029 / 22030 / 483 | 94.13% (93.85%-94.41%) | 82.18% (80.73%-83.59%) | 95.54% (95.26%-95.81%) | 68.41% (66.75%-69.98%) | 97.85% (97.67%-98.05%) | 74.66% (73.46%-75.83%) |
| P6:STACH | 21 | 725 / 25045 | 618 / 184 / 24861 / 107 | 98.87% (98.74%-99.00%) | 85.24% (82.55%-87.89%) | 99.27% (99.16%-99.37%) | 77.06% (74.02%-80.00%) | 99.57% (99.48%-99.66%) | 80.94% (78.62%-83.08%) |
| P8:AFIB | 50 | 675 / 25095 | 632 / 136 / 24959 / 43 | 99.31% (99.20%-99.41%) | 93.63% (91.70%-95.50%) | 99.46% (99.36%-99.55%) | 82.29% (79.34%-84.90%) | 99.83% (99.78%-99.88%) | 87.60% (85.65%-89.39%) |
| P8:PAC | 30 | 539 / 25231 | 332 / 1635 / 23596 / 207 | 92.85% (92.54%-93.16%) | 61.60% (57.48%-65.67%) | 93.52% (93.20%-93.82%) | 16.88% (15.20%-18.53%) | 99.13% (99.01%-99.24%) | 26.50% (24.11%-28.74%) |
| P8:PVC | 60 | 1067 / 24703 | 822 / 596 / 24107 / 245 | 96.74% (96.53%-96.96%) | 77.04% (74.58%-79.56%) | 97.59% (97.40%-97.79%) | 57.97% (55.38%-60.64%) | 98.99% (98.87%-99.11%) | 66.16% (64.01%-68.35%) |
| P8:RBBB | 106 | 710 / 25060 | 669 / 722 / 24338 / 41 | 97.04% (96.83%-97.25%) | 94.23% (92.48%-95.89%) | 97.12% (96.91%-97.33%) | 48.09% (45.38%-50.77%) | 99.83% (99.78%-99.88%) | 63.68% (61.10%-66.04%) |
| P8:SB | 22 | 2711 / 23059 | 2396 / 1232 / 21827 / 315 | 94.00% (93.70%-94.29%) | 88.38% (87.10%-89.56%) | 94.66% (94.36%-94.95%) | 66.04% (64.45%-67.56%) | 98.58% (98.41%-98.74%) | 75.60% (74.35%-76.71%) |
| P8:STACH | 21 | 725 / 25045 | 637 / 276 / 24769 / 88 | 98.59% (98.44%-98.73%) | 87.86% (85.26%-90.25%) | 98.90% (98.76%-99.03%) | 69.77% (66.70%-72.77%) | 99.65% (99.56%-99.72%) | 77.78% (75.47%-79.95%) |

### Ranking and calibration metrics

| Endpoint | AUROC (95% CI) | Average precision (95% CI) | Brier score (95% CI) | ECE (95% CI) |
| --- | ---: | ---: | ---: | ---: |
| P4:ASMI | 0.8762 (0.8386-0.9107) | 0.0526 (0.0299-0.0966) | 0.1745 (0.1723-0.1766) | 0.3615 (0.3589-0.3640) |
| P4:IMI | 0.9088 (0.8815-0.9319) | 0.1435 (0.0887-0.2154) | 0.2510 (0.2478-0.2542) | 0.4295 (0.4262-0.4327) |
| P4:LVH | 0.7943 (0.7625-0.8232) | 0.0503 (0.0350-0.0747) | 0.3466 (0.3434-0.3498) | 0.5235 (0.5202-0.5269) |
| P6:AFIB | 0.9987 (0.9983-0.9990) | 0.9433 (0.9236-0.9607) | 0.0092 (0.0083-0.0100) | 0.0157 (0.0145-0.0169) |
| P6:PVC | 0.9562 (0.9496-0.9626) | 0.6539 (0.6228-0.6855) | 0.0410 (0.0394-0.0426) | 0.0791 (0.0767-0.0814) |
| P6:RBBB | 0.9875 (0.9830-0.9913) | 0.8064 (0.7750-0.8355) | 0.0357 (0.0341-0.0374) | 0.0711 (0.0690-0.0733) |
| P6:SB | 0.9687 (0.9658-0.9714) | 0.8117 (0.7956-0.8266) | 0.1111 (0.1085-0.1138) | 0.1795 (0.1761-0.1831) |
| P6:STACH | 0.9919 (0.9862-0.9955) | 0.8787 (0.8531-0.9034) | 0.0175 (0.0165-0.0186) | 0.0386 (0.0370-0.0402) |
| P8:AFIB | 0.9987 (0.9983-0.9990) | 0.9426 (0.9227-0.9602) | 0.0088 (0.0080-0.0097) | 0.0174 (0.0162-0.0187) |
| P8:PAC | 0.8496 (0.8283-0.8702) | 0.2895 (0.2480-0.3342) | 0.0723 (0.0710-0.0738) | 0.1992 (0.1970-0.2014) |
| P8:PVC | 0.9728 (0.9680-0.9775) | 0.7039 (0.6731-0.7329) | 0.0397 (0.0382-0.0412) | 0.0897 (0.0875-0.0919) |
| P8:RBBB | 0.9896 (0.9851-0.9935) | 0.8809 (0.8581-0.9011) | 0.0269 (0.0254-0.0284) | 0.0471 (0.0451-0.0491) |
| P8:SB | 0.9795 (0.9778-0.9812) | 0.8470 (0.8335-0.8595) | 0.0464 (0.0445-0.0484) | 0.0514 (0.0490-0.0540) |
| P8:STACH | 0.9902 (0.9850-0.9942) | 0.8702 (0.8451-0.8939) | 0.0230 (0.0218-0.0243) | 0.0499 (0.0481-0.0516) |

## Historical selected-profile comparison

| Profile | Evaluation unit and denominator | Decision policy | Accuracy (definition) | Macro-F1 | Disposition and limit |
| --- | --- | --- | ---: | ---: | --- |
| Primary6 (P6) | 1,643 selected ECG | Record-level top-1; thresholded membership sets reported separately. | 1,564/1,643 = 95.19% (record-level top-1) | 80.09% (binary-panel macro-F1) | Diagnostic profile; V3H informed model selection, so not an untouched test. |
| Primary8 (P8) | 2,193 selected ECG, including the P6 cohort | Record-level top-1; forced fallback if the threshold set is empty (58 selected-cohort cases). | 1,987/2,193 = 90.61% (record-level top-1) | 76.14% (binary-panel macro-F1) | Candidate; does not pass the complete project gate. |
| Primary4 (P4) | 962 selected binary-panel observations across 733 ECG / 676 linked patients | Per-class checkpoint thresholds; binary panel observations are the unit. | 80.23% (mean binary-panel accuracy) | 79.35% (binary-panel macro-F1) | Selected high-confidence panels; accepted by project decision, not independent clinical validation. |

The P8 denominator overlaps P6 and must not be summed with it. P4 observations are not unique ECGs or patients. The reported canonical metrics are not proof of patient-disjoint training or exact historical loader reproduction; see [checkpoint-to-patient lineage](CHECKPOINT_TO_PATIENT_SPLIT_LINEAGE.md) and [replay disposition](HISTORICAL_LOADER_IDENTITY_AND_REPLAY.md).

## Sources and reproduction

- SPH endpoint data: [`outputs/results/external_sph/sph_aggregate_normalized_32669.json`](../../outputs/results/external_sph/sph_aggregate_normalized_32669.json)
- SPH endpoint definitions: [`docs/external_validation/sph_label_harmonization.md`](../external_validation/sph_label_harmonization.md)
- Rhythm profile results: [`outputs/results/primary/canonical_profiles.json`](../../outputs/results/primary/canonical_profiles.json)
- P4 panel metrics: [`outputs/results/external_dev/pathology_primary4_metrics.json`](../../outputs/results/external_dev/pathology_primary4_metrics.json)
- P4 panel denominator: [`data/external_dev/pathology/release_cohort_report.json`](../../data/external_dev/pathology/release_cohort_report.json)
- Rebuild this proposal with `python scripts/evaluation/export_reviewer_proposed_tables.py`.
- The SPH target represents a recorded ECG statement; no code does not mean clinical absence. Quarantine was not assessed. The SPH transfer does not establish full historical source independence.
