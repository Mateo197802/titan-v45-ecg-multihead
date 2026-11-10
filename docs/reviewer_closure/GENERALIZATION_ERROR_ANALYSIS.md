# Generalization Error Analysis

**Scope:** Aggregate errors in the already completed SPH ECG-statement transfer; not an independent clinical-validation experiment.
**Source:** [`GENERALIZATION_PER_CLASS_METRICS.json`](GENERALIZATION_PER_CLASS_METRICS.json), reproducibly derived from the versioned SPH aggregate.

## Endpoint-level error interpretation

The SPH reference positives are uncommon for several endpoints. For example, P8 PAC has 539 positive statements among 25,770 records. At the released operating point, it has 332 TP, 1,635 FP and 207 FN: precision 16.88%, recall 61.60%, F1 26.50%, AUROC 0.8496. Ranking discrimination does not remove the low positive predictive value at this prevalence and threshold.

P4 uses the same 25,770-record statement-source denominator for each compatible endpoint, but the statement support is only 91 ASMI, 209 LVH and 120 IMI positives. The corresponding confusion counts are:

| Endpoint | Positive support | TP | FP | FN | Precision | Recall | F1 | AUROC |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| P4 ASMI | 91 | 56 | 2,219 | 35 | 2.46% | 61.54% | 4.73% | 0.8762 |
| P4 LVH | 209 | 150 | 7,869 | 59 | 1.87% | 71.77% | 3.65% | 0.7943 |
| P4 IMI | 120 | 107 | 6,365 | 13 | 1.65% | 89.17% | 3.25% | 0.9088 |

These are statement-level proxy results under the frozen threshold vector, not adjudicated disease outcomes. High sensitivity or AUROC cannot be described as high positive predictive value. The historical 962-row balanced P4 panel is a different population and denominator; it must not be pooled with these 25,770-row endpoints.

For rhythm endpoints, the aggregated pattern also separates ranking from a fixed decision threshold. P6 RBBB has 686 TP, 1,067 FP and 24 FN (precision 39.13%, recall 96.62%, F1 55.70%). P6 PVC has 905 TP, 1,375 FP and 162 FN (precision 39.69%, recall 84.82%, F1 54.08%). These counts support a descriptive error profile; they do not identify why individual errors occurred.

## What cannot be inferred

- Aggregate false positives/negatives do not reveal clinical cause, waveform morphology, reader disagreement or a patient-specific failure mechanism.
- The independent point-level check verifies aggregate metrics from restricted inputs but does not license publishing individual ECGs or identifiers.
- The 79 errors recorded in the P6 gate audit are counts without source-specific denominators; they cannot be converted to source error rates or causal domain-shift claims.
- No threshold optimization, class remapping, record removal or post-hoc correction was performed for this analysis.

## Reproducible detail

The JSON records TP/TN/FP/FN, supports, all metric values, patient-cluster bootstrap intervals, valid/invalid replicate counts and prespecified exact-duplicate sensitivity by endpoint. Regenerate it with `scripts/evaluation/export_generalization_per_class_metrics.py`; the source aggregate SHA-256 is embedded. Any new interpretation remains bounded to the existing SPH statement-transfer study.
