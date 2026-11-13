# Primary results: reserved CODE-15%

The supervised Transformer + ResNet adaptation was evaluated on 4,921 ECGs
from 3,891 held-out patients within CODE-15%, separately from training,
validation and calibration patients. Published P6 and P8 were scored on
the same eligible ECGs, reference flags and five endpoints.

| System | Macro-F1 (patient IC95%) | Macro-AUROC | Macro-AUPRC | Mean binary accuracy | Macro-Brier | Macro-ECE |
|---|---|---:|---:|---:|---:|---:|
| Published P6 | 0.347962 [0.319967, 0.374958] | 0.924045 | 0.357411 | 0.922983 | 0.104780 | 0.157275 |
| Published P8 | 0.370366 [0.339554, 0.400351] | 0.931114 | 0.390036 | 0.914367 | 0.095117 | 0.142728 |
| Adapted Transformer + ResNet | **0.602658 [0.564561, 0.634111]** | **0.978102** | **0.579463** | **0.983052** | **0.014944** | **0.014245** |

Paired macro-F1 differences were +0.254696 vs P6 (95% CI [0.222034, 0.288306])
and +0.232291 vs P8 ([0.197721, 0.268708]). Differences are computed before
rounding. The systems use different locked thresholds, so these differences
do not isolate the effect of changing model weights.

| Endpoint | Positive ECGs | F1 | AUROC | AUPRC | Binary accuracy | Sensitivity | PPV |
|---|---:|---:|---:|---:|---:|---:|---:|
| AFIB | 101 | 0.541063 | 0.959946 | 0.512495 | 0.980695 | 0.554455 | 0.528302 |
| SB | 64 | 0.465753 | 0.982287 | 0.439918 | 0.984150 | 0.531250 | 0.414634 |
| STACH | 110 | 0.657040 | 0.987321 | 0.684675 | 0.980695 | 0.827273 | 0.544910 |
| RBBB | 133 | 0.825623 | 0.985815 | 0.811194 | 0.990043 | 0.872180 | 0.783784 |
| 1AVB | 82 | 0.523810 | 0.975138 | 0.449032 | 0.979679 | 0.670732 | 0.429688 |

The adapted system missed 45/101 AFIB and 30/64 SB positives. AFIB sensitivity
fell vs both published profiles; SB reduced false positives substantially but
also lost true positives. For 1AVB, false positives increased from 27 (P8)
to 73, and PPV fell. RBBB had the highest adapted F1. STACH gained PPV but
lost one true positive vs each baseline. The 0.70 research target and the
prespecified safeguards were not met: **no promotion**.

Accuracy is the mean of five binary accuracies, not multiclass accuracy
or an ECG-level all-label match rate. With positive support between 64 and
133 ECGs, negatives dominate that measure. AUROC and AUPRC are ranking
metrics and do not imply high recall at the deployed cut. The source reports
no macro interval for AUROC, AUPRC, accuracy, Brier or ECE; these are
`NOT_AVAILABLE`, not inferred from per-class intervals.
