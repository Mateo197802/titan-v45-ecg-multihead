# R1-1 disposition: not scientifically closed

The first CODE-15% archive adds executed, paired, external-source
agreement estimates for five compatible rhythm endpoints. It does not
establish population-wide performance, waveform duration as specified,
historical patient independence, or independent clinical adjudication.
Do not change the historical PR #3 rubric; this is supplemental PR #6
evidence.

| Point | What PR #6 demonstrates | What remains |
|---|---|---|
| R1-1 | Frozen weights scored on the same 1,442 ECGs, with reference and patient intervals; both observed promotion gates fail. | All 18 archives; duration source reconciliation; defensible historical patient independence and separate confirmation if development changes. |
| R2-3a | One CODE archive has exact index membership; a fixed patient hash retains repeat ECGs; overlap screened on aligned signals. MIMIC's own patient partitions are disjoint. | Source-patient identity across datasets, historical training manifests, untested overlaps and unresolved waveform contract. |
| R2-4a | Per-class metrics, confusion, support, calibration and paired IC95% for the first archive. | Complete denominator and reference coverage across 18 archives; no claim of adjudicated clinical accuracy. |
| R2-general | Five explicitly compatible rhythm endpoints; no Other or P4 score evaluation under CODE. | Additional endpoints require separate explicit positive and negative references. |
| R2-4e | Five-endpoint binary calls and empty-set counts under unchanged thresholds. | These counts do not measure P8 top-1 fallback, an operational full cascade or clinical quarantine. |

MIMIC has [a waveform QC receipt](../../outputs/results/external_validation_20261111/MIMIC_QC_33295.json),
a [development grammar audit](MIMIC_DEVELOPMENT_GRAMMAR_AUDIT.md), and
[completed inference without references](../../outputs/results/external_validation_20261111/MIMIC_LABEL_BLIND_INFERENCE_33296.json)
on 6,675 ECGs from 4,077 patients for all three profiles. This is not
reference-backed performance. The parser yielded zero explicit negatives;
its missed variants are not evidence for treating silence as absence.
The independent cohort and P4 options remain subject to
[access and label feasibility](INDEPENDENT_CONFIRMATORY_VALIDATION.md).
