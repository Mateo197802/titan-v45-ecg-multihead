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

## Illustrative prevalence sensitivity

The [prevalence-only projection](../../outputs/results/benchmarkmax/sph_prevalence_projection_v1.json)
uses the frozen SPH statement-level sensitivity and specificity at each
original threshold. At hypothetical 1% and 5% statement prevalence, the
projected PPV is respectively 67.80% and 91.65% for P6 AFIB, 8.76% and
33.35% for P8 PAC, 6.71% and 27.26% for P4 ASMI, 2.30% and 10.93% for P4
LVH, and 3.50% and 15.90% for P4 IMI. At the observed prevalence it reproduces
the actual statement-level PPV.

These are algebraic scenarios, not measured results in another population.
They assume sensitivity, specificity, case mix and annotation process remain
comparable as prevalence changes, and do not include uncertainty intervals.
This is not evidence of disease prevalence, clinical performance, a pure
prior-probability shift, or that prevalence alone caused the observed gaps.
Recompute without changing the frozen baseline using:

```bash
python scripts/benchmarkmax/analyze_prevalence_shift.py \
  --input outputs/results/benchmarkmax/sph_baseline_diagnostic_32726.json \
  --output /path/to/new/projection.json
```

CEDIA CPU job `32730` independently reran this exact aggregate calculation
from commit `b8a4ce2` and exited `0:0`. Its output and the published JSON
both have SHA-256
`5112a891b24ddcc3c71478723ecbad3a4a4301adb2aec2788df118569f508c93`.
This verifies deterministic execution, not an independent patient cohort.

SPH may be used as a disclosed adaptation/development source only with
patient-separated splits and a predeclared analysis. A distinct eligible source
is needed for any confirmatory external-generalization claim after adaptation.
The separate [B1 calibration diagnostic](B1_SPH_CALIBRATION_RESULTS.md) has
since been completed on these previously observed frozen scores. It is a
score-only exploratory analysis, not a newly trained V4.6 specialist or
independent validation. Brier/ECE were lower than the raw scores, but nested
F1 decisions were unchanged, AUROC/AP shifted slightly down, and no
constant-prevalence comparator was included. Thus no model improvement or
incremental probability value over prevalence alone is established. No V4.6
checkpoint or trained specialist exists yet.
