# R1-1 disposition: not scientifically closed

**R1-1: PARTIAL.** The [full locked CODE-15% comparison](CODE15_FULL_EVALUATION.md)
adds executed, paired, external-source agreement estimates for five
compatible rhythm endpoints across all 18 ZIPs in the frozen sample.
It does not establish performance across all source patients, verified
10 s waveforms, historical patient independence or independent clinical
adjudication. This is supplemental PR #6 evidence; the historical PR #3
rubric is unchanged.

| Point | What PR #6 demonstrates | What remains |
|---|---|---|
| R1-1 | Frozen weights scored on the same 24,682 ECGs from 17,300 patients, with reference and paired patient intervals. Both promotion gates fail. | Source-backed duration, historical patient independence and separate confirmation on eligible, unexamined data. |
| R2-3a | Exact HDF5-to-index membership in all 18 CODE archives; a fixed patient hash retains repeat ECGs; overlap screened on aligned signals. MIMIC's own patient partitions are disjoint. | Source-patient identity across datasets, historical training manifests, untested overlaps and unresolved waveform contract. |
| R2-4a | Per-class metrics, confusion, support, calibration and paired 95% confidence intervals for the full frozen sample. | No claim of adjudicated clinical accuracy or unrestricted source performance. |
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
