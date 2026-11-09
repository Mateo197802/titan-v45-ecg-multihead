# Observed SPH baseline diagnostic

This is a retrospective, exploratory diagnostic of the V4.5 SPH evaluation
whose results have already been observed. It is not a new independent test,
not an improvement claim, and does not select a threshold, model or cohort.
CEDIA job `32726` checked the frozen ledger and aggregate hashes and reconciled
all five confusion matrices. It emitted the [aggregate diagnostic](../../outputs/results/benchmarkmax/sph_baseline_diagnostic_32726.json)
without individual ECG or patient identifiers.

All 25,770 ECG and 24,666 source patients are included. Positives mean a coded
ECG statement; a negative means that statement is not recorded, not an
adjudicated absence of disease. Thus a false positive below is a disagreement
with the recorded statement, not necessarily a clinical misdiagnosis.

| Endpoint | Statement prevalence / no-skill AP | TP | FP | FN | PPV | AUROC | AP | Brier | ECE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| P6 AFIB | 2.62% | 628 | 112 | 47 | 84.86% | 0.9987 | 0.9433 | 0.0092 | 0.0157 |
| P8 PAC | 2.09% | 332 | 1,635 | 207 | 16.88% | 0.8496 | 0.2895 | 0.0723 | 0.1992 |
| P4 ASMI | 0.35% | 56 | 2,219 | 35 | 2.46% | 0.8762 | 0.0526 | 0.1745 | 0.3615 |
| P4 LVH | 0.81% | 150 | 7,869 | 59 | 1.87% | 0.7943 | 0.0503 | 0.3466 | 0.5235 |
| P4 IMI | 0.47% | 107 | 6,365 | 13 | 1.65% | 0.9088 | 0.1435 | 0.2510 | 0.4295 |

The low statement prevalence, substantial discordant-positive counts and
observed calibration errors are consistent with a difficult transfer operating
point. They do not isolate causation: label incompleteness, reference ontology,
data shift, preprocessing and training exposure remain possible explanations.
The high AUROC values alone do not establish that recalibration will solve the
low PPV or F1. The 20-bin curves in the diagnostic are descriptive approximations
on previously inspected SPH data, not a protocol for selecting thresholds.

## Diagnostic figures

- [ROC](../../outputs/figures/benchmarkmax/sph_baseline_roc.png) ([PDF](../../outputs/figures/benchmarkmax/sph_baseline_roc.pdf))
- [Precision-recall](../../outputs/figures/benchmarkmax/sph_baseline_pr.png) ([PDF](../../outputs/figures/benchmarkmax/sph_baseline_pr.pdf))
- [Statement calibration](../../outputs/figures/benchmarkmax/sph_baseline_calibration.png) ([PDF](../../outputs/figures/benchmarkmax/sph_baseline_calibration.pdf))
- [Score distributions](../../outputs/figures/benchmarkmax/sph_baseline_score_distributions.png) ([PDF](../../outputs/figures/benchmarkmax/sph_baseline_score_distributions.pdf))

ROC and precision-recall lines use the 20-bin aggregates; legend AUROC and AP
come from the original unbinned aggregate, not numerical integration of those
lines. The [manifest](../../outputs/figures/benchmarkmax/figure_manifest.json)
records SHA-256 for the input, generator and outputs. Recreate them with:

```bash
python scripts/benchmarkmax/plot_sph_baseline.py \
  --input outputs/results/benchmarkmax/sph_baseline_diagnostic_32726.json \
  --output-dir outputs/figures/benchmarkmax
```

Image bytes can depend on the plotting environment, especially PDF metadata;
the manifest certifies the published files, not bitwise identity across runs.

SPH may be used as a disclosed adaptation/development source only with
patient-separated splits and a predeclared analysis. A distinct eligible source
is needed for any confirmatory external-generalization claim after adaptation.
No V4.6 checkpoint, calibration method or improved result exists yet.
